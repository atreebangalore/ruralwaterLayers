from qgis.core import QgsJsonExporter
from qgis.utils import iface
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsPointXY, QgsGeometry, QgsWkbTypes, QgsCoordinateReferenceSystem, QgsProcessingUtils, QgsProcessingContext, QgsRasterLayer
from PyQt5.QtCore import QVariant
from qgis import processing

lat = 27.86915
long = 76.91920
eff_height = 2.99

fabdem = r'G:/Shared drives/Jaltol/TBS_Jaltol Fellow/Ishita - Analysis + Data/GIS_files/Johad_Structures/Rasters/FABDEM/Elevation_FABDEM.tif'
fabdem_flow_acc = r'G:/Shared drives/Jaltol/TBS_Jaltol Fellow/Ishita - Analysis + Data/GIS_files/Johad_Structures/Rasters/FABDEM/Flow_Accumulation_FABDEM.tif'
fabdem_drain_dir = r'G:/Shared drives/Jaltol/TBS_Jaltol Fellow/Ishita - Analysis + Data/GIS_files/Johad_Structures/Rasters/FABDEM/Drainage_Direction_FABDEM.tif'

def point_layer(latitude, longitude):
    print(f'creating point layer for latitude {latitude} and longitude {longitude}')
    point = QgsPointXY(longitude, latitude)
    layer = QgsVectorLayer('Point?crs=EPSG:4326', 'my_point', 'memory')
    pr = layer.dataProvider()
    fields = [QgsField('Longitude', QVariant.Double), QgsField('Latitude', QVariant.Double)]
    pr.addAttributes(fields)
    layer.updateFields()
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPointXY(point))
    feature.setAttributes([longitude, latitude])
    pr.addFeature(feature)
    layer.updateExtents()
    QgsProject.instance().addMapLayer(layer)
    print('point layer added.')
    return layer

def processing2lyr(output_layer_id, lyr_name):
    context = QgsProcessingContext()
    output_layer = QgsProcessingUtils.mapLayerFromString(output_layer_id, context)
    # Add the output layer to the QGIS map
    QgsProject.instance().addMapLayer(output_layer)
    output_layer.setName(lyr_name)

def catchment_delineation(lat, long, drain_dir_path):
    print('processing the r.water.outlet for catchment layer')
    params = {'GRASS_RASTER_FORMAT_META' : '',
            'GRASS_RASTER_FORMAT_OPT' : '',
            'GRASS_REGION_CELLSIZE_PARAMETER' : 0,
            'GRASS_REGION_PARAMETER' : None,
            'coordinates' : f'{long},{lat} [EPSG:4326]',
            'input' : drain_dir_path,
            'output' : 'TEMPORARY_OUTPUT' }
    result = processing.run("grass7:r.water.outlet", params)
    output_layer_id = result['output']
    processing2lyr(output_layer_id, 'catchment_delineated')
    print('catchment delineation completed.')
    return output_layer_id

def catchment_polygonize(catchment_raster_path):
    print('processing catchment raster to vector')
    params = {'INPUT':catchment_raster_path,
            'BAND':1,
            'FIELD':'val',
            'EIGHT_CONNECTEDNESS':False,
            'EXTRA':'',
            'OUTPUT':'TEMPORARY_OUTPUT'}
    result = processing.run("gdal:polygonize", params)
    output_layer_id = result['OUTPUT']
    processing2lyr(output_layer_id, 'catchment_polygonized')
    print('catchment polygonization completed.')
    return output_layer_id

def mask_dem(dem_path, polygon_path):
    print('processing elevation raster masking by catchment vector')
    params = {'INPUT':dem_path,
              'MASK':polygon_path,
              'SOURCE_CRS':None,
              'TARGET_CRS':None,
              'TARGET_EXTENT':None,
              'NODATA':None,
              'ALPHA_BAND':False,
              'CROP_TO_CUTLINE':False,
              'KEEP_RESOLUTION':False,
              'SET_RESOLUTION':False,
              'X_RESOLUTION':None,
              'Y_RESOLUTION':None,
              'MULTITHREADING':False,
              'OPTIONS':'',
              'DATA_TYPE':0,
              'EXTRA':'',
              'OUTPUT':'TEMPORARY_OUTPUT'}
    result = processing.run("gdal:cliprasterbymasklayer", params)
    output_layer_id = result['OUTPUT']
    processing2lyr(output_layer_id, 'elevation_masked')
    print('masking elevation to catchment completed.')
    return output_layer_id

def low_elev_point(pt_lyr, masked_elev_path):
    print('processing lowerst elevation pixel')
    params = {'INPUT':pt_lyr.source(),
     'RASTERCOPY':masked_elev_path,
     'COLUMN_PREFIX':'SAMPLE_',
     'OUTPUT':'TEMPORARY_OUTPUT'}
    result = processing.run("native:rastersampling", params)
    output_layer = result['OUTPUT']
    elevation_value = [feature['SAMPLE_1'] for feature in output_layer.getFeatures()][0]
    print(f'lowest elevation value = {round(elevation_value,2)}m')
    return elevation_value

def dem_polygonize(masked_elev_path):
    print('processing elevation masked raster to polygons')
    params = {'INPUT_RASTER':masked_elev_path,
              'RASTER_BAND':1,
              'FIELD_NAME':'VALUE',
              'OUTPUT':'TEMPORARY_OUTPUT'}
    result = processing.run("native:pixelstopolygons", params)
    output_layer = result['OUTPUT']
    QgsProject.instance().addMapLayer(output_layer)
    output_layer.setName('elevation_polygonized')
    print('polygonizing masked elevation completed.')

def main(dem, drain_dir):
    pt_lyr = point_layer(lat, long)
    catchment_raster_path = catchment_delineation(lat, long, drain_dir)
    catchment_poly_path = catchment_polygonize(catchment_raster_path)
    masked_elev_path = mask_dem(dem, catchment_poly_path)
    dem_polygonize(masked_elev_path)
    lowest_elev = low_elev_point(pt_lyr, masked_elev_path)

print('started...')
main(fabdem, fabdem_drain_dir)
print('completed!!!')