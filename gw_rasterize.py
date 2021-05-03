import sys
from pathlib import Path
import lib.gw_utils as gwmod
import config.groundwater as gwcfg
import numpy as np
import pandas as pd
import logging

from shapely.geometry import Point, LineString, Polygon
import geopandas as gpd

import geojson
import json

from qgis.core import (
    QgsApplication,
    QgsExpression,
    QgsFeatureRequest,
    QgsProcessingFeedback,
    QgsVectorLayer,
    QgsVectorFileWriter
)
from qgis.analysis import QgsNativeAlgorithms

import rasterio
import re

def main():
    """reads in a pre-processed groundwater layer, with recharge-discharge (CSV) and returns tif
    
    Args:
        state(str): state for which well elevations must be obtained
        season(str): e.g. rech-96, disc-96
        
    Returns:
        None: well elevations with locations stored in CSV as SHP
    
    """
    state = sys.argv[1]
    season = sys.argv[2]
    dataPath = Path.cwd().joinpath("data","groundwater")
    metaPath = Path.cwd().joinpath("outputs","groundwater","csv",state+"_metadata.log")
    outputsPath = Path.cwd().joinpath("outputs","groundwater")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    
    logging.info("get Recharge-Discharge for '%s' dataset",state)

    QgsApplication.setPrefixPath("G:\\Users\\Craig\\miniconda3\\envs\\geo_env\\Library\\python\\qgis", True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    # Append the path where processing plugin can be found
    sys.path.append('G:\\Users\\Craig\\miniconda3\\envs\\geo_env\\Library\\python\\plugins')
    import processing
    from processing.core.Processing import Processing
    Processing.initialize()
    feedback = QgsProcessingFeedback()
    
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    vectorPath = outputsPath.joinpath("shapefiles",state+"_processed_wRD.shp")
    print(vectorPath,vectorPath.exists())
    vLayer = QgsVectorLayer(str(vectorPath), 'well_rech_disc_layer', 'ogr') #.setSubsetString(season + " IS NOT NULL")
    print("islayer valid:", vLayer.isValid())
    
    # subset layer
    filter = "\"" + season + "\"" + " IS NOT NULL"
    expr = QgsExpression(filter)
    subset = vLayer.getFeatures(QgsFeatureRequest(expr))
    vLayer.selectByIds([k.id() for k in subset])  # why didn't direct selection work? addFeature (false)
    print(vLayer.selectedFeatureCount())
    
    # write subsetted layer
    subsetPath = outputsPath.joinpath("shapefiles","noNulls",state+"_"+season+"_noNulls.shp")
    _writer = QgsVectorFileWriter.writeAsVectorFormat(vLayer, str(subsetPath), "utf-8", vLayer.crs(), "ESRI Shapefile", onlySelected=True)
    
    # import subsetted layer
    subLayer = QgsVectorLayer(str(subsetPath), 'well_rech_disc_layer_nonulls', 'ogr') 
    print("is sub layer valid:", subLayer.isValid())
    
    params = {
        'INPUT':subLayer,
        'POWER':2,    # FOR gridinversedistance
#         'RADIUS':0.25,    # FOR gridinversedistancenearestneighbor / gridlinear
#         'RADIUS_1':0.25,    # FOR gridinversedistance / gridnearestneighbor / gridaverage
#         'RADIUS_2':0.25,    # FOR gridinversedistance  /  gridnearestneighbor / gridaverage
        'MAX_POINTS':12,    # FOR gridinversedistance 
        'MIN_POINTS':1,    # FOR gridinversedistance / gridaverage
        'NODATA': NODATA,
        'Z_FIELD':season,
        'OUTPUT':str(outputsPath.joinpath("tif","noNulls",state+"_"+season+"_grid_id_min_1_max_12_nonulls.tif"))
    }
    
    res = processing.run("gdal:gridinversedistance",params,feedback=feedback)
    print(type(res['OUTPUT']))

if __name__=='__main__':
    main()

