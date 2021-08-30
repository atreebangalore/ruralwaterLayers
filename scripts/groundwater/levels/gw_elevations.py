"""STEP 2: gw_elevations computes elevations for a point shape file of well locations

reads in a pre-processed groundwater layer (SHP) from STEP 1 and returns elevations,
depth-to-water (above MSL) for each

Typical usage (terminal)
$ python layers/groundwater/levels/gw_elevations.py [ST]
check outputs folder "outputs/groundwater/csv" and "outputs/groundwater/shapefiles"

"""

import sys
from pathlib import Path

root = Path(__file__).parent.parent.parent.parent.absolute() # find project root
#sys.path.append(str(root))    # this allows lib and config modules below to be found

import gw_utils as gwmod
import config.groundwater as gwcfg
import numpy as np
import pandas as pd
import geopandas as gpd
import logging

def main():
    """reads in a pre-processed groundwater layer (SHP) and returns elevations , depth-to-water (above MSL) for each 
    
    Args:
        state(str): state for which well elevations must be obtained
        
    Returns:
        None: well elevations with locations stored in CSV as SHP
    
    """
    state = sys.argv[1]
    metaPath = root.joinpath("outputs","groundwater","csv",state+"_metadata.log")
    outputsPath = root.joinpath("outputs","groundwater")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    
    logging.info("get Elevations for '%s' dataset",state)
    path,metacols = gwcfg.get_params(state)
    
    # Initialize Well Data Object (which has self.df and self.gdf (geodataframe))
    gwObj = gwmod.WellDataObj(path,metacols)
    logging.info("original df and gdf initialized, shape: %s",str(gwObj.df.shape))

    # Get Elevation above M.S.L. for each lat,long, add elev column to self.gdf
    gwObj.get_elevations()
    logging.info("elevations obtained for %s well locations",state)
    gwObj.compute_elevations()
    logging.info("depth (wrt MSL) computed for %s well locations",state)

    dfePath = outputsPath.joinpath("csv",state+"_processed_wElev.csv")
    gdfePath = outputsPath.joinpath("shapefiles",state+"_processed_wElev.shp")

    # SAVE FILES TO CSV AND SHP
    dfe = pd.DataFrame(gwObj.gdf)
    gdfe = gwObj.gdf
    
    logging.info("saving water depths to CSV and SHP")
    dfe.to_csv(dfePath,index=False)
    logging.info("single state %s CSV processed and saved to file %s",state,str(dfePath))
    gdfe.to_file(gdfePath,index=False)
    logging.info("single state %s SHP processed and saved to file %s",state,str(gdfePath))
    
if __name__=='__main__':
    main()