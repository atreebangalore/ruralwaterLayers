"""STEP 4: gw_levels_Rasterize reads in a pre-processed groundwater LEVELS layer (CSV) and returns tif
reads in a pre-processed groundwater LEVELS layer (STEP 1 o/p) (CSV) and returns tif

Typical usage (in terminal from root directory)
$ python layers/groundwater/levels/gw_levels_rasterize.py [ST] [MONTH]  # MONTH e.g. may-96, nov-96
check outputs folder "outputs/groundwater/tif"

REQUIRES THE python qgis module installed in current virtual environment

"""

import sys
from pathlib import Path

root = Path.home() # find project root
config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]
opPath = root.joinpath("Code","atree","outputs","groundwater","levels","preprocessed")
tifPath = root.joinpath("Code","atree","outputs","groundwater","levels","tif")
print("data saved in :",opPath)

import gw_utils
import groundwater as gw_config
import numpy as np
import pandas as pd
import logging

from shapely.geometry import Point, LineString, Polygon
import geopandas as gpd

import geojson
import json

from qgis.core import (
    QgsApplication,
    QgsCoordinateTransformContext,
    QgsExpression,
    QgsFeatureRequest,
    QgsProcessingFeedback,
    QgsVectorLayer,
    QgsVectorFileWriter
)
from qgis.analysis import QgsNativeAlgorithms

import rasterio
import re
import os

def main():
    """reads in a pre-processed groundwater layer, with recharge-discharge (CSV) and returns tif
    
    Args:
        state(str): state for which well elevations must be obtained
        month(str): e.g. may-96, dec-96
        
    Returns:
        None: well elevations with locations stored in CSV as SHP
    
    """
    states = sys.argv[1].replace("[","").replace("]","").split(",")
    states_str = "_".join(states)
    
    month = sys.argv[2]
    
    metaPath = opPath.joinpath(states_str+"_metadata.log")
    
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        handlers=[logging.FileHandler(str(metaPath))],
                       )
    logging.info("get levels for '%s' dataset",states_str)

    # Initialize QGIS Application
    pythonpath = os.environ['PYTHONPATH'].split(";")[0]  # "C:\\Users\\[User]\\miniconda3\\envs\\geo_env\\Library\\python\\
    idx = pythonpath.index("python") + 7
    qgispath = pythonpath[:idx] + "qgis"
    pluginspath = pythonpath[:idx] + "plugins" 
    
    # Initialize QGIS application using python module
    QgsApplication.setPrefixPath(qgispath, True)
    qgs = QgsApplication([], False)
    qgs.initQgis()
    
    # Initialize QGIS processing plugin
    sys.path.append(pluginspath)
    import processing
    from processing.core.Processing import Processing
    Processing.initialize()
    feedback = QgsProcessingFeedback()
    
    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())

    # Get file with depth to water level values
    vectorPath = opPath.joinpath("shapefiles",states_str+"_processed_wData.shp")
    print(vectorPath,vectorPath.exists())
    vLayer = QgsVectorLayer(str(vectorPath), 'well_levels_layer', 'ogr') #.setSubsetString(month + " IS NOT NULL")
    print("islayer valid:", vLayer.isValid())
    
    # subset layer for the chosen month and choose only non null values
    filter = "\"" + month + "\"" + " IS NOT NULL"
    expr = QgsExpression(filter)
    subset = vLayer.getFeatures(QgsFeatureRequest(expr))
    vLayer.selectByIds([k.id() for k in subset])  # why didn't direct selection work? addFeature (false)
    print(vLayer.selectedFeatureCount())
    
    # write subsetted layer to shapefile
    subsetPath = opPath.joinpath("shapefiles_noNulls",states_str+"_"+month+"_noNulls.shp")
    svOptions = QgsVectorFileWriter.SaveVectorOptions()
    svOptions.driverName = "ESRI Shapefile"
    svOptions.fileEncoding = "utf-8"
    svOptions.onlySelectedFeatures = True
#     _writer = QgsVectorFileWriter.writeAsVectorFormat(vLayer, str(subsetPath), vLayer.crs(),driverName= "ESRI Shapefile",onlySelectedFeatures=True)
    _writer = QgsVectorFileWriter.writeAsVectorFormatV2(vLayer,str(subsetPath), QgsCoordinateTransformContext(), svOptions)
    
    # import subsetted layer
    subLayer = QgsVectorLayer(str(subsetPath), 'well_levels_layer_nonulls', 'ogr') 
    print("is sub layer valid:", subLayer.isValid())
    
    # declare algorithm and params for grid layer 
    # https://gdal.org/tutorials/gdal_grid_tut.html
    gridalg = "gdal:gridinversedistance"
    params = gw_config.grid_params(gridalg)
    print(params)
    params['INPUT'] = subLayer
    params['Z_FIELD'] = month
    params['OUTPUT'] = str(tifPath.joinpath(states_str+"_"+month+"_idw_grid_id_min_1_max_12_nonulls.tif"))
    
    # run processing algorithm
    res = processing.run(gridalg,params,feedback=feedback)
    print(res['OUTPUT'])

if __name__=='__main__':
    main()


####    PROBLEM WITH qgis utils    ####
# PS C:\Users\Craig D\Code\atree> python layers/groundwater/levels/gw_Rasterize.py KA rech-15
# G:\Users\Craig\miniconda3\envs\geo_env\Library\python\qgis\utils.py:793: DeprecationWarning: the imp module is d
# eprecated in favour of importlib; see the module's documentation for alternative uses
#   mod = _builtin_import(name, globals, locals, fromlist, level)
# Logged warning: Duplicate provider native registered
