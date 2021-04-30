import os
import sys
from pathlib import Path
import lib.gw_utils as gwmod
import config.groundwater as gwcfg
import numpy as np
import pandas as pd
import geopandas as gpd
import logging
from shapely.geometry import Point, LineString, Polygon
import geojson
import json

import rasterio
from geocube.api.core import make_geocube
from geocube.rasterize import rasterize_points_griddata, rasterize_points_radial
import re
from functools import partial

def main():
    dataset = sys.argv[1]
    state = sys.argv[2]
    try:
        param = sys.argv[3]
    except:
        param=None
    print("preProcessing '",dataset,"' dataset")
    path,metacols = gwcfg.get_params(dataset,state,param)
    
    # Initialize Well Data Object (df and gdf)
    gwObj = gwmod.WellDataObj(path,metacols)
    logging.info("df and gdf initialized, shape: %s",str(gwObj.df.shape))
    
    # MAKE LIST OF Data COLUMNS
    print(gwObj.dataCols)

#     # DECLARE STATE BOUNDARY
#     with open(Path.cwd().joinpath("outputs","final","shapefiles","KA_boundary.geojson")) as f:
#         geom = geojson.load(f)
#         fea = geom["features"][0]['geometry']
#         state_boundary = json.dumps(fea)
    
#     print(gwObj.gdf.loc[:,["rech-96","geometry"]].dropna(how='any'))
    
    # FOR LOOP FOR YEARS
    for col in gwObj.dataCols[0:2]:
        tifPath = Path.cwd().joinpath("outputs","final","tif",state + "_" + dataset + "_" + col + ".tif")
        print(tifPath)
        # first run of this, with entire gdf gave memory error, shows steps involved in rasterizing layer
        cube = make_geocube(vector_data=gwObj.gdf.loc[:,[col,"geometry"]].dropna(how='any'), 
                            resolution=(-0.001, 0.001),
                            interpolate_na_method='cubic',
                            rasterize_function=partial(rasterize_points_griddata, method="cubic"))
        cube[col].rio.to_raster(tifPath)

if __name__=='__main__':
    main()