import os
import sys
from pathlib import Path
import lib.gw_utils as gwmod
import config.groundwater as gwcfg
import numpy as np
import pandas as pd
import geopandas as gpd
import logging
from shapely.geometry import Point, LineString, Polygon


def main():
    dataset = sys.argv[1]
    state = sys.argv[2]
    try:
        param = sys.argv[3]
    except:
        param=None
    print("preProcessing '",dataset,"' dataset")
    path,metacols = gwcfg.get_params(dataset,state,param)
    radius = 5
    
    dfePath = Path.cwd().joinpath("outputs","final","csv",state+"_processed_wElev.csv")
    dfdPath = Path.cwd().joinpath("outputs","final","csv",state+"_processed_wDiff.csv")
    metaPath = Path.cwd().joinpath("outputs","final","csv",state+"_metadata.log")
    gdfePath = Path.cwd().joinpath("outputs","final","shapefiles",state+"_processed_wElev.shp")
    gdfdPath = Path.cwd().joinpath("outputs","final","shapefiles",state+"_processed_wDiff.shp")
    tifPath = Path.cwd().joinpath("outputs","final","tif",state+"_processed.tif")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    
    # Initialize Well Data Object (df and gdf)
    gwObj = gwmod.WellDataObj(path,metacols)
    logging.info("df and gdf initialized, shape: %s",str(gwObj.df.shape))
    
    # Subset gdf to a single state
    gwObj.subset_gdf(state)
    logging.info("single state subsetted : %s , no of records: %d",state,len(gwObj.gdf))
    
    # Remove Duplicates (entire row)  ,Remove Null Data Rows,  Drop Duplicate geometries
    num_dups,num_nulls,num_geom_dups = gwObj.pre_process()
    logging.info("number of duplicates found & dropped: %d \
                 number of nulls found & dropped: %d \
                 number of duplicate geometries found & dropped: %d",num_dups,num_nulls,num_geom_dups)
    
    # Get Elevation above M.S.L. for each lat,long, add elev column to self.gdf
    gwObj.get_elevations()
    logging.info("elevations obtained for %s well locations",state)
    gwObj.compute_elevations()
    logging.info("depth (wrt MSL) computed for %s well locations",state)
    
    # Compute annual recharge and discharge for all wells
    rd = gwObj.recharge_discharge()
    print(rd.columns)
    logging.info("recharge-discharge computed for %s well locations",state)
    
    # Make self.gdf_proj by Projecting self.gdf and add 5m buffer geometry to self.gdf_proj
    # gwObj.buffer_geoms(radius)
    # logging.info("buffer circles of radius %d mts created",radius)
    
    # SAVE FILES TO CSV AND SHP
    dfe = pd.DataFrame(gwObj.gdf)
    gdfe = gwObj.gdf

    dfD = pd.DataFrame(gwObj.gdf_diff)
    gdfD = gwObj.gdf_diff
    
    logging.info("saving water depths to CSV and SHP")
    dfe.to_csv(dfePath,index=False)
    logging.info("single state %s CSV processed and saved to file %s",state,str(dfePath))
    gdfe.to_file(gdfePath,index=False)
    logging.info("single state %s SHP processed and saved to file %s",state,str(gdfePath))
    # saving self.gdf_proj doesn't work
    # error TypeError: Cannot interpret '<geopandas.array.GeometryDtype object at 0x000001E0C4AD4F48>' as a data type
    
    logging.info("saving recharge/discharge to CSV and SHP")
    dfD.to_csv(dfdPath,index=False)
    logging.info("single state %s CSV processed and saved to file %s",state,str(dfdPath))
    gdfD.to_file(gdfdPath,index=False)
    logging.info("single state %s SHP processed and saved to file %s",state,str(gdfdPath))
    
if __name__=='__main__':
    main()



