import os,sys
from pathlib import Path
import json
import ee
ee.Initialize()

root = Path.home() # find project root
config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]
import geeassets    # from Code/atree/config
import placenames

class BoundaryWiseStats:
    """
    class to handle an image collection , 
    aggregate it as required, monthly/yearly etc
    then return stats for a feature collection's polygons
    """
    
    def __init__(self,spatial_stat,temporal_stat,temporal_step,dataset,year):
        self.spatial_stat = spatial_stat
        self.temporal_stat = temporal_stat
        self.temporal_step = temporal_step
        self.dataset = dataset
        self.year = year
        
        print("\nThis script computes the '" + self.temporal_stat + " " + self.temporal_step + 
          " " + self.dataset + "' images for the hydrological year of '" + str(self.year) + "'")
        print("It then takes the " + self.temporal_step + " image/images and computes the district-wise '" + 
          self.spatial_stat + "' of all pixels in each district ")
        
    def set_chosen_states(self,chosen_states):
        self.chosen_states = chosen_states
        self.chosen_states = [placenames.ST_names[ST] for ST in self.chosen_states]
        print("\nchosen states:",self.chosen_states)
        
    def set_boundary_label(self,boundaries_label):
        self.boundaries_label = boundaries_label
        
    def set_image_coll(self):
        self.iCollDict = geeassets.iCollDict[self.dataset]
        print("\nSelected image collection: ", self.iCollDict.limit(1).getInfo()['id'])
        
    def get_stat_dict(self):
        self.statDict = geeassets.statDict  # reducers 'total','min','max','mean'..

    def make_date_range_list(self): 
        if (self.temporal_step == 'monthly'):
            # list of months in hydro year - [6,..,12,1,..,5]
            months1 = ee.List.sequence(6,12)
            months2 = ee.List.sequence(1,5)

            dr1 = months1.map(
                lambda m: ee.Date.fromYMD(self.year,m,1).getRange('month'))
            dr2 = months2.map(
                lambda m: ee.Date.fromYMD(self.year+1,m,1).getRange('month'))
            self.drl = dr1.cat(dr2)
        else:
            start = ee.Date.fromYMD(self.year,6,1)
            end = ee.Date.fromYMD(self.year+1,6,1)
            self.drl = ee.List([ee.DateRange(start,end)])
        #print(self.drl)
        return self.drl
    
    def filter_image_coll(self):
        start = ee.Date.fromYMD(self.year,6,1)
        end = ee.Date.fromYMD(self.year+1,6,1)
        self.iColl_filtered = self.iCollDict.filterDate(start,end)
        print(self.iColl_filtered.size().getInfo(),
              "images filtered for the hydrological year",self.year)
        
        self.sample_image = self.iColl_filtered.first()
        self.proj = self.sample_image.projection()
        self.scale = self.proj.nominalScale()
        #print("Projection of calculation: ",self.proj.getInfo())
        #print("Correct Scale of calculation: ", self.scale.getInfo())
    
    def set_temporal_reducer(self):
        self.tempReducer = self.statDict.get(self.temporal_stat)
        #print("temp reducer",self.tempReducer.getInfo())
        
    def set_spatial_reducer(self):
        self.spatialReducer = self.statDict.get(self.spatial_stat)
        #print("spatial reducer",self.spatialReducer.getInfo())
    
    def get_column_names(self):
        self.state_col = geeassets.fCollDict['districts']['state_col']        # "State"
        self.district_col = geeassets.fCollDict['districts']['district_col']  # "District_N"
    
    def get_boundary_polygon(self):
        ######       Boundary Polygon      ######
        self.boundaries = geeassets.fCollDict['districts']['id']
        self.boundaries = self.boundaries.filter(
            ee.Filter.inList(self.state_col,self.chosen_states))
        print("\nno of district polygons:",self.boundaries.size().getInfo())



    def temp_reduce_image_coll(self):
        def temp_reduce_image(dr):
            start = ee.DateRange(dr).start()
            end = ee.DateRange(dr).end()
        
            mimages = self.iColl_filtered.filter(ee.Filter.date(start,end)).select(0)
            mimages_reduced = mimages.reduce(self.tempReducer)
            mimages_reduced = mimages_reduced.set(
                'system:time_start', start.millis()).set(
                'system:time_end', end.millis())

            return ee.Image(mimages_reduced)
        
        self.iColl_reduced = self.drl.map(temp_reduce_image)
        print("\nno of monthly images:",self.iColl_reduced.size().getInfo())
        return self.iColl_reduced.getInfo()

    def set_export_vars(self):
        ######         Export Vars        #####
        export_columns = [self.state_col,self.district_col,self.spatial_stat]    
        export_folder = 'gee_exports'
        #print(export_columns,export_folder)
        
    def get_boundarywisestats(self):
        self.bws = self.iColl_reduced.map(
            lambda image:
                ee.Image(image).reduceRegions(
                collection= self.boundaries,
                reducer= self.spatialReducer,
                scale= self.scale,
                crs= self.proj
            ).set(
                "year",ee.Date(ee.Image(image).get("system:time_start")).get('year'))
            .set(
                "month",ee.Date(ee.Image(image).get("system:time_start")).get('month'))
        )
        return self.bws

        
        
