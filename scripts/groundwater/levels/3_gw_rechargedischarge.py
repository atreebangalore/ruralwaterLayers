"""STEP 3: gw_RechargeDischarge computes recharge discharge for a point shape file of well locations

reads in a pre-processed groundwater layer (STEP 1 o/p) (CSV) and returns monsoon recharge, non-monsoon discharge for all years

Typical usage (in terminal from root directory)
$ python layers/groundwater/levels/3_gw_rechargedischarge.py [ST]    #[KA,TN]
check outputs folder "outputs/groundwater/tif"

"""

import sys
from pathlib import Path

root = Path.home() # find project root
config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]
opPath = root.joinpath("Code","atree","outputs","groundwater","levels","preprocessed")
print("data saved in :",opPath)

import gw_utils as gwmod
import config.groundwater as gwcfg
import numpy as np
import pandas as pd
import geopandas as gpd
import logging

def main():
    """reads in a pre-processed groundwater layer, with depth to water (above MSL) (CSV) and returns monsoon recharge, non-monsoon discharge 
    
    Args:
        state(str): states or [list,of,states] for which well elevations must be obtained
        
    Returns:
        None: well recharge,discharge with locations stored in CSV as SHP
    
    """
    states = sys.argv[1].replace("[","").replace("]","").split(",")    # [KA,MH] (str) -> [KA,MH] (list) 
    states_str = "_".join(states)    # KA_MH
    
    metaPath = opPath.joinpath(states_str+"_metadata.log")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    logging.info("get Recharge-Discharge for '%s' dataset",states_str)
    
    # get path of data file and cols to extract
    path,metacols = gwcfg.get_params(states_str)
    
    # Initialize Well Data Object (df and gdf)
    # Well Data Object handles the original data file CSV using df and gdf structures
    gwObj = gwmod.WellDataObj(path,metacols)
    logging.info("original df and gdf initialized, shape: %s",str(gwObj.df.shape))

    # Compute annual recharge and discharge for all wells
    rd = gwObj.recharge_discharge()
    logging.info("recharge-discharge computed for %s well locations",states_str)

    # Assign output paths
    dfdPath = opPath.joinpath(states_str+"_processed_wRD.csv")
    gdfdPath = opPath.joinpath("shapefiles",states_str+"_processed_wRD.shp")

    # SAVE FILES TO CSV AND SHP
    dfd = pd.DataFrame(gwObj.gdf_diff)
    gdfd = gwObj.gdf_diff
    
    logging.info("saving Recharge Discharge to CSV and SHP")
    dfd.to_csv(dfdPath,index=False)
    logging.info(" %s CSV processed and saved to file %s",states_str,str(dfdPath))
    gdfd.to_file(gdfdPath,index=False)
    logging.info(" %s SHP processed and saved to file %s",states_str,str(gdfdPath))
    
if __name__=='__main__':
    main()