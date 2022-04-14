"""
This script generates the [temporal_statistic] total/mean/median/.. for iColl images for a chosen [temporal_step] year , months etc
then returns a CSV of the [spatial_statistic] mean/median/..etc. values per image for each district in the [chosen_states]

e.g. python getBoundaryWiseStats.py median total monthly rainfall 2018 upp-ganga-basin [KA,TN]

"""
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
import BoundaryWiseStats as BWS


def main():

    #####        Inputs - General            #####
    spatial_stat = sys.argv[1]        #median OR # one of 'total','mean','median','min','max'
    temporal_stat = sys.argv[2]       #total OR  # one of 'total','mean','median','min','max'
    temporal_step = sys.argv[3]       #monthly OR # one of 'yearly','monthly'
    dataset = sys.argv[4]             #rainfall OR # 'evapotranspiration','groundwater_levels'
    year = int(sys.argv[5])           #2018
    boundaries_label = sys.argv[6]    #no-space-name for chosen boundary, e.g. KA, krishna_basin 
                              
    ######      Inputs - Boundary Subset      #####     
    # ['DL','MP','HR','HP','RJ','UP','UT'] # Upper Ganga Basin
    chosen_states = sys.argv[7].replace("[","").replace("]","").split(",") 
    print(chosen_states)
    
    ######      Instantiate Class             ######
    bws = BWS.BoundaryWiseStats(spatial_stat,temporal_stat,temporal_step,dataset,year)
    
    bws.set_chosen_states(chosen_states)
    bws.set_boundary_label(boundaries_label)
    bws.set_image_coll()
    bws.get_stat_dict()
    drl = bws.make_date_range_list()
    print("date range list: ",drl.getInfo())
    bws.filter_image_coll()
    bws.set_temporal_reducer()
    bws.set_spatial_reducer()
    bws.get_column_names()
    bws.get_boundary_polygon()
    bws.set_export_vars()
    iColl_reduced = bws.temp_reduce_image_coll()
    stats = bws.get_boundarywisestats()
#     print(stats.getInfo().keys())
    
if __name__=="__main__":
    main()