""" STEP 1: gw_preProcess preProcesses single state's groundwater data

reads groundwater levels data directory
subsets single state
preprocesses file
saves single state to csv and shp in outputs/groundwater
STEP 2: gw_elevations

Typical usage (in terminal from root directory)
$ python layers/groundwater/levels/gw_preProcess.py [ST]

"""

import sys
from pathlib import Path

root = Path(__file__).parent.parent.parent.parent.absolute() # find project root
#sys.path.append(str(root))    # this allows lib and config modules below to be found

import gw_utils as gwmod
import config.groundwater as gwcfg
import logging


def main():
    """reads in a groundwater levels dataset and pre-processes it.
    
    preprocessing involves subsetting by State if needed, removing nulls, duplicates
    and duplicate geometries, then saving to CSV, SHP (with data) and SHP (geoms only)
    
    Args:
        state (str): optional, two letter short names for a state to be subsetted
        
    Returns:
        None: preprocessed data saved to outputs folder
    """
    state = sys.argv[1]
    metaPath = root.joinpath("outputs","groundwater","csv",state+"_metadata.log")
    outputsPath = root.joinpath("outputs","groundwater")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    
    logging.info("preProcessing '%s' dataset",state)
    path,metacols = gwcfg.get_params(state)
    
    # Initialize Well Data Object (which has self.df and self.gdf (geodataframe))
    gwObj = gwmod.WellDataObj(path,metacols)
    logging.info("original df and gdf initialized, shape: %s",str(gwObj.df.shape))
    
    # Subset gdf to a single state
    gwObj.subset_gdf(state)
    logging.info("single state subsetted : %s , no of records: %d",state,len(gwObj.gdf))
    
    # Remove Duplicates (entire row)  ,Remove Null Data Rows,  Drop Duplicate geometries
    num_dups,num_nulls,num_geom_dups = gwObj.pre_process()
    logging.info("number of duplicates found & dropped: %d \
                 number of nulls found & dropped: %d \
                 number of duplicate geometries found & dropped: %d",num_dups,num_nulls,num_geom_dups)
    
    # Save processed dataframe to CSV , SHP(without data) and SHP(with data) 
    dfPath = outputsPath.joinpath("csv", (state + '_processed' + path.suffix))
    gdfPath = outputsPath.joinpath("shapefiles", (state + '_processed' + ".shp"))
    gdfPathwData = outputsPath.joinpath("shapefiles", (state + '_processed_wData' + ".shp"))
    
    gwObj.df.to_csv(dfPath,index=False)
    logging.info("saved df to CSV")
    gwObj.gdf.geometry.to_file(gdfPath,index=False)
    logging.info("saved gdf (only geometries) to SHP")
    gwObj.gdf.to_file(gdfPathwData,index=False)
    logging.info("saved gdf (with data) to SHP")
    

if __name__=='__main__':
    main()



