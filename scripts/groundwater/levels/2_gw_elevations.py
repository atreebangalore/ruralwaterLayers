"""STEP 2: gw_elevations computes elevations for a point shape file of well locations

reads in a pre-processed groundwater layer (SHP) from STEP 1 and returns elevations,
depth-to-water (above MSL) for each

Typical usage (terminal)
$ python layers/groundwater/levels/gw_elevations.py [ST]
[ST] = [KA,MH]  # WON'T WORK FOR FULL COUNTRY BECAUSE OF GEE LIMIT
check outputs folder "{Home Dir}/Code/atree/outputs/groundwater/levels/preprocessed"
"""

import sys
from pathlib import Path

root = Path.home() # find project root
config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]
opPath = root.joinpath("Code","atree","outputs","groundwater","levels","preprocessed")
# print("data saved in :",opPath)

import gw_utils as gwmod
import groundwater as gwcfg
import pandas as pd
import logging

def main():
    """reads in a pre-processed groundwater layer (SHP) and 
    returns elevations of depth-to-water (above MSL) as csv and shp
    
    Args:
        state(str): states or [list,of,states] for which well elevations must be obtained
    
    Example:
    python Code/atree/scripts/groundwater/levels/2_gw_elevations.py KA,MH
    
    Returns:
        None: well elevations with locations as CSV and SHP at
        {Home Dir}/Code/atree/outputs/groundwater/levels/preprocessed
    
    """
    states = sys.argv[1].replace("[","").replace("]","").split(",")    # [KA,MH] (str) -> [KA,MH] (list) 
    states_str = "_".join(states)    # KA_MH
    
    metaPath = opPath.joinpath(states_str+"_metadata.log")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    logging.info("get Elevations for '%s' dataset",states_str)
    
    # get path of data file and cols to extract
    path,metacols = gwcfg.get_params(states_str)
    
    # Initialize Well Data Object (which has self.df and self.gdf (geodataframe))
    # Well Data Object handles the original data file CSV using df and gdf structures
    gwObj = gwmod.WellDataObj(path,metacols)
    logging.info("original df and gdf initialized, shape: %s",str(gwObj.df.shape))

    # Get Elevation above M.S.L. for each lat,long, add elev column to self.gdf
    gwObj.get_elevations()
    logging.info("elevations obtained for %s well locations",states_str)
    gwObj.compute_elevations()
    logging.info("depth (wrt MSL) computed for %s well locations",states_str)

    # Assign output paths
    dfePath = opPath.joinpath(states_str+"_processed_wElev.csv")
    gdfePath = opPath.joinpath("shapefiles",states_str+"_processed_wElev.shp")

    # SAVE FILES TO CSV AND SHP
    dfe = pd.DataFrame(gwObj.gdf)
    gdfe = gwObj.gdf
    
    logging.info("saving water depths to CSV and SHP")
    dfe.to_csv(dfePath,index=False)
    logging.info("%s CSV processed and saved to file %s",states_str,str(dfePath))
    gdfe.to_file(gdfePath,index=False)
    logging.info("%s SHP processed and saved to file %s",states_str,str(gdfePath))
    
if __name__=='__main__':
    main()