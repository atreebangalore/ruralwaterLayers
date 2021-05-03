import sys
from pathlib import Path
import lib.gw_utils as gwmod
import config.groundwater as gwcfg
import logging


def main():
    """reads in a groundwater levels dataset and pre-processes it.
    
    preprocesses involves subsetting by state if needed, removing nulls, duplicates
    and duplicate geometries, then saving to CSV and SHP (with data), SHP (geoms only)
    
    Args:
        state (str): optional, two letter short names for a state to be subsetted
        
    Returns:
        None: preprocessed data saved to outputs folder
    """
    state = sys.argv[1]
    metaPath = Path.cwd().joinpath("outputs","groundwater","csv",state+"_metadata.log")
    outputsPath = Path.cwd().joinpath("outputs","groundwater")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    
    logging.info("preProcessing '%s' dataset",state)
    path,metacols = gwcfg.get_params(state)
    
    # Initialize Well Data Object (df and gdf)
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



