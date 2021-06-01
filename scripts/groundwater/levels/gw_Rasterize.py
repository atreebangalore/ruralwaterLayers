"""STEP 4: gw_rasterize computes elevations for a point shape file of well locations

reads in a pre-processed groundwater layer, with recharge-discharge (CSV) and returns tif

Typical usage (in terminal from root directory)
$ python layers/groundwater/levels/gw_rasterize.py [ST] [SEASON]  # SEASON e.g. rech-96, disc-96
check outputs folder "outputs/groundwater/tif"

"""

import sys
from pathlib import Path

root = Path(__file__).parent.parent.parent.parent.absolute() # find project root
sys.path.append(str(root))    # this allows lib and config modules below to be found

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
    dataPath = root.joinpath("data","groundwater")
    metaPath = root.joinpath("outputs","groundwater","csv",state+"_metadata.log")
    outputsPath = root.joinpath("outputs","groundwater")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    
    logging.info("get Recharge-Discharge for '%s' dataset",state)

    # Initialize QGIS Application
    QgsApplication.setPrefixPath("G:\\Users\\Craig\\miniconda3\\envs\\geo_env\\Library\\python\\qgis", True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    # Append the path where QGIS processing plugin can be found
    sys.path.append('G:\\Users\\Craig\\miniconda3\\envs\\geo_env\\Library\\python\\plugins')
    import processing
    from processing.core.Processing import Processing
    Processing.initialize()
    feedback = QgsProcessingFeedback()
    
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    # Get file with recharge-discharge values from previous step
    vectorPath = outputsPath.joinpath("shapefiles",state+"_processed_wRD.shp")
    print(vectorPath,vectorPath.exists())
    vLayer = QgsVectorLayer(str(vectorPath), 'well_rech_disc_layer', 'ogr') #.setSubsetString(season + " IS NOT NULL")
    print("islayer valid:", vLayer.isValid())
    
    # subset layer for the chosen season and choose only non null values
    filter = "\"" + season + "\"" + " IS NOT NULL"
    expr = QgsExpression(filter)
    subset = vLayer.getFeatures(QgsFeatureRequest(expr))
    vLayer.selectByIds([k.id() for k in subset])  # why didn't direct selection work? addFeature (false)
    print(vLayer.selectedFeatureCount())
    
    # write subsetted layer to shapefile
    subsetPath = outputsPath.joinpath("shapefiles","noNulls",state+"_"+season+"_noNulls.shp")
    _writer = QgsVectorFileWriter.writeAsVectorFormat(vLayer, str(subsetPath), "utf-8", vLayer.crs(), "ESRI Shapefile", onlySelected=True)
    
    # import subsetted layer
    subLayer = QgsVectorLayer(str(subsetPath), 'well_rech_disc_layer_nonulls', 'ogr') 
    print("is sub layer valid:", subLayer.isValid())
    
    # declare params for grid layer 
    # https://gdal.org/tutorials/gdal_grid_tut.html
    params = {
        'INPUT':subLayer,
        'POWER':2,    # FOR gridinversedistance
#         'RADIUS':0.25,    # FOR gridinversedistancenearestneighbor / gridlinear
#         'RADIUS_1':0.25,    # FOR gridinversedistance / gridnearestneighbor / gridaverage
#         'RADIUS_2':0.25,    # FOR gridinversedistance  /  gridnearestneighbor / gridaverage
        'MAX_POINTS':12,    # FOR gridinversedistance 
        'MIN_POINTS':1,    # FOR gridinversedistance / gridaverage
        'NODATA': -9999,
        'Z_FIELD':season,
        'OUTPUT':str(outputsPath.joinpath("tif","idw",state+"_"+season+"_grid_id_min_1_max_12_nonulls.tif"))
    }
    
    res = processing.run("gdal:gridinversedistance",params,feedback=feedback)
    print(res['OUTPUT'])

if __name__=='__main__':
    main()


# PS C:\Users\Craig D\Code\atree> python layers/groundwater/levels/gw_Rasterize.py KA rech-15
# G:\Users\Craig\miniconda3\envs\geo_env\Library\python\qgis\utils.py:793: DeprecationWarning: the imp module is d
# eprecated in favour of importlib; see the module's documentation for alternative uses
#   mod = _builtin_import(name, globals, locals, fromlist, level)
# Logged warning: Duplicate provider native registered

# layers/groundwater/levels/gw_Rasterize.py:96: DeprecationWarning: QgsVectorFileWriter.writeAsVectorFormat() is d
# eprecated
#   _writer = QgsVectorFileWriter.writeAsVectorFormat(vLayer, str(subsetPath), "utf-8", vLayer.crs(), "ESRI Shapef
# ile", onlySelected=True)
# _writer = QgsVectorFileWriter.writeAsVectorFormatV2(vLayer, str(subsetPath), "utf-8", vLayer.crs(), "ESRI Shapefile", onlySelected=True)
