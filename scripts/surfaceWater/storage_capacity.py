from qgis.core import QgsJsonExporter
from qgis.utils import iface
from qgis.core import QgsProject, QgsVectorLayer, QgsField, QgsFeature, QgsPointXY, QgsGeometry, QgsWkbTypes, QgsCoordinateReferenceSystem, QgsProcessingUtils, QgsProcessingContext
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
    # Create a point
    point = QgsPointXY(longitude, latitude)

    # Create a memory layer to store the point
    layer = QgsVectorLayer('Point?crs=EPSG:4326', 'my_point', 'memory')
    pr = layer.dataProvider()

    # Add attribute fields (optional)
    fields = [QgsField('Longitude', QVariant.Double), QgsField('Latitude', QVariant.Double)]

    pr.addAttributes(fields)
    layer.updateFields()

    # Create a new feature
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPointXY(point))
    feature.setAttributes([longitude, latitude])

    # Add the feature to the layer
    pr.addFeature(feature)

    # Update Extent (optional)
    layer.updateExtents()

    # Add the layer to the map
    QgsProject.instance().addMapLayer(layer)
    print('point layer added.')

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

def main():
    point_layer(lat, long)
    catchment_delineation(lat, long, fabdem_drain_dir)

print('started...')
main()
print('completed!!!')