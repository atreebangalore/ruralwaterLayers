import sys
from pathlib import Path
import lib.gw_utils as gwmod
import config.groundwater as gwcfg
import numpy as np
import pandas as pd
import geopandas as gpd
import logging

def main():
    """reads in a pre-processed groundwater layer, with depth to water (above MSL) (CSV) and returns monsoon recharge, non-monsoon discharge 
    
    Args:
        state(str): state for which well elevations must be obtained
        
    Returns:
        None: well recharge,discharge with locations stored in CSV as SHP
    
    """
    state = sys.argv[1]
    metaPath = Path.cwd().joinpath("outputs","groundwater","csv",state+"_metadata.log")
    outputsPath = Path.cwd().joinpath("outputs","groundwater")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    
    logging.info("get Recharge-Discharge for '%s' dataset",state)
    path,metacols = gwcfg.get_params(state)
    
    # Initialize Well Data Object (df and gdf)
    gwObj = gwmod.WellDataObj(path,metacols)
    logging.info("original df and gdf initialized, shape: %s",str(gwObj.df.shape))

    # Compute annual recharge and discharge for all wells
    rd = gwObj.recharge_discharge()
    logging.info("recharge-discharge computed for %s well locations",state)

    dfdPath = outputsPath.joinpath("csv",state+"_processed_wRD.csv")
    gdfdPath = outputsPath.joinpath("shapefiles",state+"_processed_wRD.shp")

    # SAVE FILES TO CSV AND SHP
    dfd = pd.DataFrame(gwObj.gdf_diff)
    gdfd = gwObj.gdf_diff
    
    logging.info("saving Recharge Discharge to CSV and SHP")
    dfd.to_csv(dfdPath,index=False)
    logging.info("single state %s CSV processed and saved to file %s",state,str(dfdPath))
    gdfd.to_file(gdfdPath,index=False)
    logging.info("single state %s SHP processed and saved to file %s",state,str(gdfdPath))
    
if __name__=='__main__':
    main()