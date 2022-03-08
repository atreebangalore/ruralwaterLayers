"""
Given the SEBOP annual ET image, extract pixel Values for chosen districts
"""
from pathlib import Path
import ee
import sys
import pandas as pd
ee.Initialize()

root = Path.home() # find project root
config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]
opPath = root.joinpath("Code","atree","outputs","equity")
opPath.mkdir(parents=True,exist_ok=True) # create if not exist

import placenames

def main():
    """
    """
    year = int(sys.argv[1])
    states = sys.argv[2].replace("[","").replace("]","").split(",")
    states_str = "_".join(states)
    
    state_col = placenames.datameet_state_col_name
    district_col = placenames.datameet_district_col_name
    
    et_col = "ET_" + str(year)
    chosen_states = [placenames.ST_names[state] for state in states]

    start = ee.Date.fromYMD(year,6,1)
    end = ee.Date.fromYMD(year+1,5,31)

    ############         Boundary Polygon        #################
    boundaries = ee.FeatureCollection("users/cseicomms/boundaries/datameet_districts_boundary_2011")
    boundaries = boundaries.filter(ee.Filter.inList(state_col,chosen_states));
    
    ############         Image Collection        #################
    iColl = ee.ImageCollection("users/cseicomms/evapotranspiration_ssebop")
    iColl_filtered = iColl.filterDate(start,end)
    proj = iColl_filtered.first().projection()
    scale = proj.nominalScale()
    image = iColl_filtered.reduce(ee.Reducer.sum())

    pixDict = image.reduceRegions(
        collection=boundaries, 
        reducer= ee.Reducer.toList(), 
        scale=scale, 
        crs= proj
        )
    
    pixDict = pixDict.select([district_col,"list"],[district_col,et_col],False).getInfo()
    districts = [elem['properties'][district_col] for elem in pixDict['features']]
    pixValues = [elem['properties'][et_col] for elem in pixDict['features']]
    
    etTable = pd.DataFrame({'districts':districts,et_col:pixValues})
    filePath = opPath.joinpath(et_col + "_" + states_str + ".csv")
    
    etTable.to_csv(filePath,index=False)
    print("file saved with filename",filePath)

if __name__=='__main__':
    main()