"""This script calculates the amount of water that can be stored by a structure
based on the elevation dataset. The inputs required are the latitude, longitude
and effective height of the structure to be entered in the script below and
the script should be executed in the QGIS workspace, please do change the 
paths for the location of the respective elevation files.

Raises:
    ValueError: raised when the elevation dataset name is not provided correctly

Returns:
    float: volume of water that can be stored by the structure
"""
from PyQt5.QtCore import QVariant
from qgis import processing
from qgis.core import QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsField, QgsFeature, QgsPointXY, QgsGeometry, QgsProcessingUtils, QgsProcessingContext, QgsExpression
from typing import Tuple

# input (change for each structure)
dataset = 'alos' # 'alos' or 'fabdem'
latitude = 27.82714
longitude = 76.90120
eff_height = 3.47

# config for data and location of required files
fabdem_px = 30 # pixel size
fabdem_flow_acc_threshold = 20
fabdem_buffer = 0.00027027 # 30m
fabdem = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Elevation_FABDEM.tif'
fabdem_flow_acc = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Flow_Accumulation_FABDEM.tif'
fabdem_drain_dir = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Drainage_Direction_FABDEM.tif'

alos_px = 12.5
alos_flow_acc_threshold = 500
alos_buffer = 0.00027027 # 30m
alos = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\ALOS\Reprojected\Elevation_ALOS_EPSG4326.tif'
alos_flow_acc = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\ALOS\Reprojected\Flow_Accumulation_ALOS.tif'
alos_drain_dir = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\ALOS\Reprojected\Drainage_Direction_ALOS.tif'

# don't change anything after this line
def point_layer(latitude: float, longitude: float, lyr_name: str) -> QgsVectorLayer:
    """
    Create a point layer at the specified latitude and longitude.

    Parameters:
    - latitude (float): Latitude of the point.
    - longitude (float): Longitude of the point.

    Returns:
    QgsVectorLayer: Created point layer.
    """
    print(f'creating point layer for latitude {latitude} and longitude {longitude}')
    point = QgsPointXY(longitude, latitude)
    layer = QgsVectorLayer('Point?crs=EPSG:4326', lyr_name, 'memory')
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

def processing2lyr(output_layer_id: str, lyr_name: str) -> None:
    """
    Add a processing output layer to the QGIS map.

    Parameters:
    - output_layer_id (str): ID of the processing output layer.
    - lyr_name (str): Name to be assigned to the layer.
    """
    context = QgsProcessingContext()
    output_layer = QgsProcessingUtils.mapLayerFromString(output_layer_id, context)
    # Add the output layer to the QGIS map
    QgsProject.instance().addMapLayer(output_layer)
    output_layer.setName(lyr_name)

def catchment_delineation(lat: float, long: float, drain_dir_path: str) -> str:
    """
    Perform catchment delineation using r.water.outlet processing algorithm.

    Parameters:
    - lat (float): Latitude of the outlet point.
    - long (float): Longitude of the outlet point.
    - drain_dir_path (str): Path to the drainage direction raster.

    Returns:
    str: ID of the output catchment layer.
    """
    print('processing the r.water.outlet for catchment layer')
    params = {
        'GRASS_RASTER_FORMAT_META' : '',
        'GRASS_RASTER_FORMAT_OPT' : '',
        'GRASS_REGION_CELLSIZE_PARAMETER' : 0,
        'GRASS_REGION_PARAMETER' : None,
        'coordinates' : f'{long},{lat} [EPSG:4326]',
        'input' : drain_dir_path,
        'output' : 'TEMPORARY_OUTPUT'
    }
    result = processing.run("grass7:r.water.outlet", params)
    output_layer_id = result['output']
    processing2lyr(output_layer_id, 'catchment_delineated')
    print('catchment delineation completed.')
    return output_layer_id

def catchment_polygonize(catchment_raster_path: str) -> str:
    """
    Polygonize the catchment raster using the gdal:polygonize processing algorithm.

    Parameters:
    - catchment_raster_path (str): Path to the catchment raster.

    Returns:
    str: ID of the output vector layer.
    """
    print('processing catchment raster to vector')
    params = {
        'INPUT':catchment_raster_path,
        'BAND':1,
        'FIELD':'val',
        'EIGHT_CONNECTEDNESS':False,
        'EXTRA':'',
        'OUTPUT':'TEMPORARY_OUTPUT'
    }
    result = processing.run("gdal:polygonize", params)
    output_layer_id = result['OUTPUT']
    processing2lyr(output_layer_id, 'catchment_polygonized')
    print('catchment polygonization completed.')
    return output_layer_id

def mask_dem(dem_path: str, polygon_path: str) -> str:
    """
    Mask the elevation raster using the catchment vector layer.

    Parameters:
    - dem_path (str): Path to the elevation raster.
    - polygon_path (str): Path to the catchment vector layer.

    Returns:
    str: ID of the output raster layer.
    """
    print('processing elevation raster masking by vector')
    params = {
        'INPUT':dem_path,
        'MASK':polygon_path,
        'SOURCE_CRS':None,
        'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:4326'), #None,
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
        'OUTPUT':'TEMPORARY_OUTPUT'
    }
    result = processing.run("gdal:cliprasterbymasklayer", params)
    return result['OUTPUT']

def low_elev_point(pt_lyr: QgsVectorLayer, masked_elev_path: str) -> float:
    """
    Extract the elevation of the lowest point within the catchment.

    Parameters:
    - pt_lyr (QgsVectorLayer): Point layer representing the outlet.
    - masked_elev_path (str): Path to the masked elevation raster.

    Returns:
    float: Elevation of the lowest point.
    """
    print('processing lowerst elevation pixel')
    params = {
        'INPUT':pt_lyr.source(),
        'RASTERCOPY':masked_elev_path,
        'COLUMN_PREFIX':'SAMPLE_',
        'OUTPUT':'TEMPORARY_OUTPUT'
    }
    result = processing.run("native:rastersampling", params)
    output_layer = result['OUTPUT']
    elevation_value = [feature['SAMPLE_1'] for feature in output_layer.getFeatures()][0]
    print(f'lowest elevation value = {round(elevation_value,2)}m')
    return elevation_value

def dem_polygonize(masked_elev_path: str) -> QgsVectorLayer:
    """
    Polygonize the masked elevation raster.

    Parameters:
    - masked_elev_path (str): Path to the masked elevation raster.

    Returns:
    QgsVectorLayer: Polygonized vector layer.
    """
    print('processing elevation masked raster to polygons')
    params = {
        'INPUT_RASTER':masked_elev_path,
        'RASTER_BAND':1,
        'FIELD_NAME':'elevation',
        'OUTPUT':'TEMPORARY_OUTPUT'
    }
    result = processing.run("native:pixelstopolygons", params)
    output_layer = result['OUTPUT']
    return output_layer

def calc_depth(lowest_elev: float, eff_height: float, elev_lyr: QgsVectorLayer) -> QgsVectorLayer:
    """
    Calculate the depth based on the elevation.

    Parameters:
    - lowest_elev (float): Elevation of the lowest point.
    - eff_height (float): Effective height.
    - elev_lyr (QgsVectorLayer): Elevation vector layer.

    Returns:
    QgsVectorLayer: Updated elevation vector layer.
    """
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

def pond_pixels(elev_lyr: QgsVectorLayer, eff_height: float) -> QgsVectorLayer:
    """
    Extract pond pixels for the structure.

    Parameters:
    - elev_lyr (QgsVectorLayer): Elevation vector layer.
    - eff_height (float): Effective height.

    Returns:
    QgsVectorLayer: Pond pixels vector layer.
    """
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

def calc_volume(pond_lyr: QgsVectorLayer, px_size: float) -> None:
    """
    Calculate the volume of water columns.

    Parameters:
    - pond_lyr (QgsVectorLayer): Pond pixels vector layer.
    - px_size (int): Pixel size.
    """
    print('calculating the volume of water columns')
    px_list = [f['depth'] for f in pond_lyr.getFeatures()]
    volume = sum(px_list) * px_size * px_size
    print(f'volume is {round(volume,2)} m3')
    print(f'capacity of storage is {round(volume/10000,2)} crore litres')

def create_buffer(point_lyr_path, buffer_distance):
    params = {
        'INPUT':point_lyr_path,
        'DISTANCE':buffer_distance,
        'SEGMENTS':5,
        'END_CAP_STYLE':0,
        'JOIN_STYLE':0,
        'MITER_LIMIT':2,
        'DISSOLVE':False,
        'OUTPUT':'TEMPORARY_OUTPUT'
    }
    result = processing.run("native:buffer", params)
    output_layer_id = result['OUTPUT']
    return output_layer_id

def intersection_poly(input_layer, reference_layer):
    # index = QgsSpatialIndex(reference_layer.getFeatures())
    input_layer.removeSelection()
    # for input_feature in input_layer.getFeatures():
    #     input_geometry = input_feature.geometry()
    #     intersecting_ids = index.intersects(input_geometry.boundingBox())
    #     for reference_id in intersecting_ids:
    #         reference_feature = reference_layer.getFeature(reference_id)
    #         reference_geometry = reference_feature.geometry()
    #         if input_geometry.intersects(reference_geometry):
    #             input_layer.select(input_feature.id())
    params = {
        'INPUT':input_layer,
        'PREDICATE':[0],
        'INTERSECT':reference_layer,
        'METHOD':0
    }
    processing.run("native:selectbylocation", params)
    selected_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "selected_pixels", "memory")
    provider = selected_layer.dataProvider()
    selected_layer.startEditing()
    fields = input_layer.fields()
    for field in fields:
        provider.addAttributes([field])
    selected_layer.updateFields()
    for feature in input_layer.selectedFeatures():
        selected_layer.addFeature(feature)
    selected_layer.commitChanges(stopEditing=True)
    input_layer.removeSelection()
    return selected_layer


def correct_point(point_lyr: QgsVectorLayer, flow_acc_path: str, buffer_distance: float, threshold: int) -> Tuple[float, float, str]:
    """
    Extract pond pixels for the structure.

    Parameters:
    - point_lyr (QgsVectorLayer): Point Layer for structure location.
    - flow_acc_path (str): Path for the flow accumulation raster.
    - buffer_distance (float): distance for surrounding pixels to consider.
    - threshold (int): Threshold for the flow accumulation value.

    Returns:
    Tuple[float, float, str]: latitude, longitude and warning message for threshold.
    """
    structure_buffer = create_buffer(point_lyr.source(), buffer_distance)
    buffer_100 = create_buffer(point_lyr.source(), 0.0009009)
    print('buffer calculation completed.')
    mask_100_path = mask_dem(flow_acc_path, buffer_100)
    elev_poly = dem_polygonize(mask_100_path)
    selected_pixels = intersection_poly(elev_poly, structure_buffer)
    max_flow = max([f['elevation'] for f in selected_pixels.getFeatures()])
    warning = ''
    if max_flow < threshold:
        warning = f'Warning: Flow Accumulation Threshold condition not satisfied. {max_flow}<{threshold}'
    for f in selected_pixels.getFeatures():
        if f['elevation'] == max_flow:
            geometry = f.geometry()
            centroid = geometry.centroid().asPoint()
            return centroid.y(), centroid.x(), warning
    return 0.0, 0.0, warning

def check_projection(raster_path: str) -> None:
    """
    Check the projection of raster and print if it does not match EPSG:4326

    Parameters:
    - raster_path (str): Path to the Raster data.
    """
    raster = QgsRasterLayer(raster_path, 'projection_check', 'gdal')
    if raster.crs() != QgsCoordinateReferenceSystem('EPSG:4326'):
        print(f'{raster.crs().authid()} is the Projection of {raster_path}')
    del raster

def main(data: str) -> None:
    """
    Main function to process data.

    Parameters:
    - data (str): Dataset identifier.
    """
    if data == 'fabdem':
        dem = fabdem
        flow_acc = fabdem_flow_acc
        drain_dir = fabdem_drain_dir
        px_size = fabdem_px
        buffer = fabdem_buffer
        threshold = fabdem_flow_acc_threshold
    elif data == 'alos':
        dem = alos
        flow_acc = alos_flow_acc
        drain_dir = alos_drain_dir
        px_size = alos_px
        buffer = alos_buffer
        threshold = alos_flow_acc_threshold
    else:
        raise ValueError('mention the dataset used!')
    print(f'\n# {data} calculation:')
    map(check_projection, (dem, flow_acc, drain_dir))
    given_pt = point_layer(latitude, longitude, 'given_point')
    lat, long, warning = correct_point(given_pt, flow_acc, buffer, threshold)
    pt_lyr = point_layer(lat, long, 'calculated_point')
    catchment_raster_path = catchment_delineation(lat, long, drain_dir)
    catchment_poly_path = catchment_polygonize(catchment_raster_path)
    masked_elev_path = mask_dem(dem, catchment_poly_path)
    processing2lyr(masked_elev_path, 'elevation_masked')
    print('masking elevation to catchment completed.')
    lowest_elev = low_elev_point(pt_lyr, masked_elev_path)
    elev_lyr = dem_polygonize(masked_elev_path)
    print('polygonizing masked elevation completed.')
    elev_lyr = calc_depth(lowest_elev, eff_height, elev_lyr)
    pond_lyr = pond_pixels(elev_lyr, eff_height)
    calc_volume(pond_lyr, px_size)
    print(warning)

print('started...')
main(dataset)
print('completed!!!')
