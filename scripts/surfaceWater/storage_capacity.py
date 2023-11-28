from qgis.core import QgsJsonExporter
from qgis.utils import iface
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsPointXY, QgsGeometry, QgsWkbTypes, QgsCoordinateReferenceSystem, QgsProcessingUtils, QgsProcessingContext, QgsRasterLayer, QgsExpression, QgsVectorLayerCache, QgsFeatureRequest
from PyQt5.QtCore import QVariant
from qgis import processing

lat = 27.86915
long = 76.91920
eff_height = 2.99

fabdem_px = 30 # pixel size
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
              'FIELD_NAME':'elevation',
              'OUTPUT':'TEMPORARY_OUTPUT'}
    result = processing.run("native:pixelstopolygons", params)
    output_layer = result['OUTPUT']
    print('polygonizing masked elevation completed.')
    return output_layer

def calc_depth(lowest_elev, eff_height, elev_lyr):
    print('Calculation of depth based on elevation being carried out')
    elev_lyr.dataProvider().addAttributes([QgsField('depth', QVariant.Double)])
    elev_lyr.updateFields()
    depth_col = elev_lyr.fields().lookupField('depth')
    for f in elev_lyr.getFeatures():
        col_val = lowest_elev + eff_height - f['elevation']
        elev_lyr.dataProvider().changeAttributeValues({f.id(): {depth_col: col_val}})
    QgsProject.instance().addMapLayer(elev_lyr)
    elev_lyr.setName('elevation_polygonized')
    return elev_lyr

def pond_pixels(elev_lyr, eff_height):
    print('extracting pond pixels for the structure')
    expression = QgsExpression(f'"depth" > 0 AND "depth" < {eff_height+1}')
    elev_lyr.setSubsetString(expression.expression())
    pond_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "pond_pixels", "memory")
    provider = pond_layer.dataProvider()
    pond_layer.startEditing()
    fields = elev_lyr.fields()
    for field in fields:
        provider.addAttributes([field])
    pond_layer.updateFields()
    for feature in elev_lyr.getFeatures():
        pond_layer.addFeature(feature)
    QgsProject.instance().addMapLayer(pond_layer)
    pond_layer.commitChanges(stopEditing=True)
    elev_lyr.setSubsetString('')
    print('pond pixels layer created')
    return pond_layer

def calc_volume(pond_lyr, px_size):
    print('calculating the volume of water columns')
    px_list = [f['depth'] for f in pond_lyr.getFeatures()]
    volume = sum(px_list) * px_size * px_size
    print(f'volume is {round(volume,2)} m3')
    print(f'capacity of storage is {round(volume/10000,2)} crore litres')

def main(dem, drain_dir, px_size):
    pt_lyr = point_layer(lat, long)
    catchment_raster_path = catchment_delineation(lat, long, drain_dir)
    catchment_poly_path = catchment_polygonize(catchment_raster_path)
    masked_elev_path = mask_dem(dem, catchment_poly_path)
    lowest_elev = low_elev_point(pt_lyr, masked_elev_path)
    elev_lyr = dem_polygonize(masked_elev_path)
    elev_lyr = calc_depth(lowest_elev, eff_height, elev_lyr)
    pond_lyr = pond_pixels(elev_lyr, eff_height)
    calc_volume(pond_lyr, px_size)

print('started...')
main(fabdem, fabdem_drain_dir, fabdem_px)
print('completed!!!')