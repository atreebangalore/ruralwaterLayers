""" STEP 1: gw_preProcess preProcesses single state's or whole country's groundwater data

reads groundwater levels data directory
subsets single state [optional]
preprocesses file
saves single state / whole country to csv and shp in outputs/groundwater/levels/preprocessed

Typical usage (in terminal from root directory)
$ python Code/atree/scripts/groundwater/levels/1_gw_preProcess.py [ST]
ST - two letter abbreviated State Names seperated by comma.
check outputs folder "Code/atree/outputs/groundwater/levels/preprocessed/" 

"""

import sys
from pathlib import Path

root = Path.home() # find project root
config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]
opPath = root.joinpath("Code","atree","outputs","groundwater","levels","preprocessed")
# print("data saved in :",opPath)

import gw_utils
import groundwater as gw_config
import logging


def main():
    """reads in a groundwater levels dataset and pre-processes it.
    
    preprocessing involves subsetting by State if needed, removing nulls, duplicates
    and duplicate geometries, then saving to CSV, SHP (with data) and SHP (geoms only)
    
    Args:
        state (str): two letter short names for a state to be subsetted, or IN for whole country
        
    Example:
    python Code/atree/scripts/groundwater/levels/1_gw_preProcess.py KA,MH
    
    Returns:
        None: preprocessed data saved to outputs folder
        {Home Dir}/Code/atree/outputs/groundwater/levels/preprocessed/
    """
    states = sys.argv[1].replace("[","").replace("]","").split(",")    # [KA,MH] (str) -> [KA,MH] (list) 
    states_str = "_".join(states)    # KA_MH

    opPath.mkdir(parents=True,exist_ok=True)
    metaPath = opPath.joinpath(states_str+"_metadata.log")
    metaPath.touch(exist_ok=True)
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                        )
    logging.info("preProcessing dataset for '%s' ",states_str)
    
    # get path of data file and cols to extract
    path,metacols = gw_config.get_params(states_str)
    
    # Initialize Well Data Object (which has self.df and self.gdf (geodataframe))
    # Well Data Object handles the original data file CSV using df and gdf structures
    gwObj = gw_utils.WellDataObj(path,metacols)
    logging.info("original df and gdf initialized, shape: %s",str(gwObj.df.shape))
    
    # Subset gdf to a single state
    gwObj.subset_gdf(states_str)
    logging.info("states subsetted : %s , no of records: %d",states_str,len(gwObj.gdf))
    
    # Remove Duplicates (entire row)  ,Remove Null Data Rows,  Drop Duplicate geometries
    num_dups,num_nulls,num_geom_dups = gwObj.pre_process()
    logging.info("number of duplicates found & dropped: %d \
                number of nulls found & dropped: %d \
                number of duplicate geometries found & dropped: %d",num_dups,num_nulls,num_geom_dups)
    
    # Save processed dataframe to CSV , SHP(without data) and SHP(with data) 
    dfPath = opPath.joinpath(states_str + '_processed' + path.suffix)
    shpPath = opPath.joinpath("shapefiles")
    shpPath.mkdir(parents=True,exist_ok=True)
    gdfPath = shpPath.joinpath((states_str + '_processed' + ".shp"))
    gdfPathwData = shpPath.joinpath((states_str + '_processed_wData' + ".shp"))
    
    gwObj.df.to_csv(dfPath,index=False)
    logging.info("saved df to CSV")
    gwObj.gdf.geometry.to_file(gdfPath,index=False)
    logging.info("saved gdf (only geometries) to SHP")
    gwObj.gdf.to_file(gdfPathwData,index=False)
    logging.info("saved gdf (with data) to SHP")
    

if __name__=='__main__':
    main()



