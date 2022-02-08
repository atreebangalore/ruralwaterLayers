import os
import sys
import datetime
from pathlib import Path
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
import geopy
import rasterio
import xlrd
import json
import ee

ee.Initialize()

class WellDataObj:
    def __init__(self,path,metacols):
        self.path = path
        self.metacols = metacols + ['geometry'] #,'elevation'
        self.long = [elem for elem in self.metacols if re.search(r"lon",elem.lower()) != None][0]    # Get name of longitude column
        self.lat = [elem for elem in self.metacols if re.search(r"lat",elem.lower()) != None][0]    # Get name of latitude column
        self.stateCol = [elem for elem in self.metacols if re.search(r"state",elem.lower()) != None][0]    # Get name of state column

        if path.suffix=='.csv':
            self.df = pd.read_csv(path) 
            self.gdf = self.make_gdf_from_df()
        elif path.suffix=='.xls':
            self.df = pd.read_excel(path,skiprows=3)
            self.df = self.df.loc[:, ~self.df.columns.str.match('Unnamed')]
            self.gdf = self.make_gdf_from_df()
        elif path.suffix=='.zip':
            self.gdf = gpd.read_file(path).loc[:,metacols]
            self.df = pd.DataFrame(self.gdf)
        else:
            print("file passed must be either csv or xls")
            pass
        self.dataCols = [elem for elem in list(self.df.columns) if re.search(r'\d+$', elem) is not None]   # Get data cols, i.e. all cols except metacols
        print(self.dataCols)
        self.gdf_diff = gpd.GeoDataFrame()
        
    def make_gdf_from_df(self):
                
        self.gdf = gpd.GeoDataFrame(self.df,
                              crs='EPSG:4326',
                              geometry=gpd.points_from_xy(self.df[self.long],self.df[self.lat])
                                   )
        return self.gdf
    
    def subset_gdf(self,states=None):
        self.states = "" if ((states is None) or (states == "IN")) else states
        
        self.states_list = self.states.split("_")
            
        if len(self.states_list[0]) > 0:
            self.df = self.df[self.df[self.stateCol].isin(self.states_list)]
            self.gdf = self.make_gdf_from_df()
        else:
            pass
        return self.gdf
    
    def remove_dups(self):
        lenBefore = len(self.df)
        self.df = self.df.drop_duplicates()
        self.num_dups = len(self.df) - lenBefore
        self.gdf = self.make_gdf_from_df()
    
    def remove_nulls(self):
        lenBefore = len(self.df)
        self.df = self.df.dropna(how='all',subset=self.dataCols)
        self.df = self.df.dropna(how='any',subset=[self.long,self.lat])
        self.num_nulls = len(self.df) - lenBefore
        self.gdf = self.make_gdf_from_df()
    
    def remove_dup_geoms(self):
        self.gdfDup = self.gdf[self.gdf.duplicated('geometry')]
        self.gdf = self.gdf.drop_duplicates('geometry')
        self.df = pd.DataFrame(self.gdf)
        self.num_geom_dups = len(self.gdfDup)
        
    def get_sample_dup_geoms(self):
        random = self.gdfDup.sample(1)
        lat = random[self.lat].iloc[0]
        long = random[self.long].iloc[0]
        original = self.df[(self.df[self.long]==long)&(self.df[self.lat]==lat)].loc[:,[self.lat,self.long]+self.dataCols]
        return original
    
    def pre_process(self):
        self.remove_dups()
        self.remove_nulls()
        self.remove_dup_geoms()
        return(self.num_dups,self.num_nulls,self.num_geom_dups)
    
    def buffer_geoms(self,buffer=20):
        self.gdf_proj = self.gdf.to_crs("EPSG:3857")
        self.gdf_proj["buffer"] = self.gdf_proj.buffer(buffer)
#         self.gdf_proj.set_geometry("buffer",inplace=True)
        return self.gdf_proj
    
    def get_elevations(self):
        srtm = ee.Image('CGIAR/SRTM90_V4')
        coll = ee.FeatureCollection(json.loads(self.gdf[['geometry']].to_json())['features'])
        elevationObj = srtm.reduceRegions(coll, ee.Reducer.mean())
        elevations = elevationObj.getInfo() # 
        edf = gpd.read_file(json.dumps(elevations))
        self.gdf = gpd.sjoin(self.gdf,edf , how="inner", op='intersects').drop(['index_right','id'],axis=1).rename(columns={'mean':'elevation'}) 
        return self.gdf
    
    def compute_elevations(self):
        for col in self.dataCols:
            self.gdf[col] = self.gdf['elevation'] - self.gdf[col]
    
    def recharge_discharge(self):
        preM = [elem for elem in self.dataCols if re.search(r"May",elem) != None]
        postM = [elem for elem in self.dataCols if re.search(r"Nov",elem) != None]
        allyrs = [elem.split("-")[1] for elem in self.dataCols]
        uyears = list(dict.fromkeys(allyrs))[:-1]
        recharge = [*zip(preM,postM,uyears)]
        discharge = [*zip(postM[:-1],preM[1:],uyears)]
        for elem in self.metacols:                            # WILL THROW ERRORS IF KEY NOT FOUND
            self.gdf_diff[elem] = self.gdf[elem]
        for pre,post,year in recharge:
            self.gdf_diff['rech-' + year] = - self.gdf[post] - (-self.gdf[pre])    # -4.78 - (-6.34)    e.g. # Nov 96 - May 96
        for post,pre,year in discharge:
            self.gdf_diff['disc-' + year] = - self.gdf[post] - (-self.gdf[pre])    # -4.78 - (-6.1)   e.g. # Nov 96 - May 97
        self.gdf_diff['geometry'] = self.gdf['geometry']
        return self.gdf_diff       
        
        
    def _merge_dup_geoms(self):
        lenBefore = len(self.df)
        self.df.index = self.df.location.rename('index')
        
        self.temp = self.df.copy()
        dupIndex = self.temp.index[self.temp.index.duplicated()]
        self.temp = self.temp.loc[:,self.dataCols].groupby('index').mean().replace(0,np.nan)
        
        self.temp = self.temp.join(self.df[self.metacols],how='left')
        self.temp = self.temp.drop_duplicates(subset=[self.stateCol]+[self.districtCol]+self.dataCols+keepCols)
        return self.temp