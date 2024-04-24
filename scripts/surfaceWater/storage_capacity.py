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
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsRasterLayer, QgsDistanceArea, QgsCoordinateReferenceSystem, QgsField, QgsFeature, QgsPointXY, QgsGeometry, QgsProcessingUtils, QgsProcessingContext, QgsExpression
from typing import Tuple, List, Dict
import pandas as pd
from collections.abc import Iterable

# input (change for each structure)
inputs = [
    ('fabdem', 26.581561, 77.289162, (2.24,3)),
]
# dataset = 'fabdem' # 'alos' or 'fabdem' or 'cartosat'
# latitude = 26.581561
# longitude = 77.289162
# eff_height = 2.24

# config for data and location of required files
fabdem_px = 30 # pixel size
fabdem_flow_acc_threshold = 20
fabdem_buffer = 0.00081081081 # 90m
# fabdem = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Elevation_FABDEM.tif'
# fabdem_flow_acc = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Flow_Accumulation_FABDEM.tif'
# fabdem_drain_dir = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Drainage_Direction_FABDEM.tif'
fabdem = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Elevation_FABDEM_Karauli.tif"
fabdem_flow_acc = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Flow_Accumulation_FABDEM_Karauli.tif"
fabdem_drain_dir = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Drainage_Direction_FABDEM_Karauli.tif"

alos_px = 12.5
alos_flow_acc_threshold = 500
alos_buffer = 0.0009009009 # 100m
alos = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\ALOS\Reprojected\Elevation_ALOS_EPSG4326.tif'
alos_flow_acc = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\ALOS\Reprojected\Flow_Accumulation_ALOS.tif'
alos_drain_dir = r'G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\ALOS\Reprojected\Drainage_Direction_ALOS.tif'

cartosat_px = 10
cartosat_flow_acc_threshold = 20000
cartosat_buffer = 0.0009009009 # 100m
cartosat = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\CartoSAT\P5_PAN_CD_N26_500_E077_250_DEM.tif"
cartosat_flow_acc = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\CartoSAT\CARTOSAT_FlowAccu.tif"
cartosat_drain_dir = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\CartoSAT\CARTOSAT_draindir.tif"

outdict = {}

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
    # processing2lyr(output_layer_id, 'catchment_delineated')
    print('catchment delineation completed.')
    return output_layer_id

def catchment_polygonize(catchment_raster_path: str, lyr_name: str) -> str:
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
    processing2lyr(output_layer_id, lyr_name)
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
    return result['OUTPUT']

def calc_depth(lowest_elev: float, eff_height: float, elev_lyr: QgsVectorLayer, lyr_name: str) -> QgsVectorLayer:
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
    column = lyr_name.replace('elevation_polygonized_','')[:10]
    elev_lyr.dataProvider().addAttributes([QgsField(column, QVariant.Double)])
    elev_lyr.updateFields()
    depth_col = elev_lyr.fields().lookupField(column)
    for f in elev_lyr.getFeatures():
        col_val = lowest_elev + eff_height - f['elevation']
        elev_lyr.dataProvider().changeAttributeValues({f.id(): {depth_col: col_val}})
    QgsProject.instance().addMapLayer(elev_lyr)
    elev_lyr.setName(lyr_name)
    return elev_lyr

def pond_pixels(elev_lyr: QgsVectorLayer, eff_height: float, lyr_name: str) -> QgsVectorLayer:
    """
    Extract pond pixels for the structure.

    Parameters:
    - elev_lyr (QgsVectorLayer): Elevation vector layer.
    - eff_height (float): Effective height.

    Returns:
    QgsVectorLayer: Pond pixels vector layer.
    """
    print('extracting pond pixels for the structure')
    column = lyr_name.replace('pond_pixels_','')[:10]
    expression = QgsExpression(f'"{column}" > 0 AND "{column}" < {eff_height+50}')
    elev_lyr.setSubsetString(expression.expression())
    pond_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", lyr_name, "memory")
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

def calc_volume(pond_lyr: QgsVectorLayer, px_size: float, column: str) -> float:
    """
    Calculate the volume of water columns.

    Parameters:
    - pond_lyr (QgsVectorLayer): Pond pixels vector layer.
    - px_size (int): Pixel size.
    """
    print('calculating the volume of water columns')
    px_list = [f[column[:10]] for f in pond_lyr.getFeatures()]
    # print(f'depth values considered for volume calculation: {px_list}')
    volume = sum(px_list) * px_size * px_size
    print(f'volume is {round(volume,2)} m3')
    print(f'capacity of storage is {round(volume/10000,2)} crore litres')
    return round(volume/10000,2)

def create_buffer(point_lyr_path: str, buffer_distance: float) -> QgsVectorLayer:
    """
    Create a buffer feature for a point location provided.

    Parameters:
    - point_lyr_path (str): Input point layer for buffer.
    - buffer_distance (float): Buffer distance.

    Returns:
    QgsVectorLayer: buffer layer.
    """
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
    return result['OUTPUT']

def intersection_poly(input_layer: QgsVectorLayer, reference_layer: str) -> QgsVectorLayer:
    """
    Extract Features in input layer that intersects the features in reference layer.

    Parameters:
    - input_layer (QgsVectorLayer): Input layer for selection of features.
    - reference_layer (str): Reference layer used for selection.

    Returns:
    QgsVectorLayer: latitude, longitude and warning message for threshold.
    """
    input_layer.removeSelection()
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

def check_threshold(threshold: float, flow_px_list: List[float]) -> Tuple[Tuple[float, ...], str]:
    """check the flow accumulation values and filter out those above threshold

    Args:
    - threshold (float): threshold value for flow accumulation
    - flow_px_list (List[float]): flow accumulation values surrounding input location

    Returns:
    Tuple[Tuple[float, ...], str]: filtered flow accumulation values
    """
    max_flow = max(flow_px_list)
    warning = ''
    if max_flow < threshold:
        warning += f'Warning: Flow Accumulation Threshold condition not satisfied. {max_flow}<{threshold}'
        min_flow = min(flow_px_list)
        threshold = max_flow - ( (max_flow - min_flow) / 2 )
        warning += f'\nNew Threshold considered is {threshold}'
    return tuple(filter(lambda x: x>=threshold, flow_px_list)), warning

def distance_feature_dict(point_lyr: QgsVectorLayer, selected_pixels: QgsVectorLayer, filtered_px: Tuple[float, ...]) -> Dict[float, QgsFeature]:
    """calculate the distances between each pixel centroid to the given point

    Parameters:
    - point_lyr (QgsVectorLayer): input given point
    - selected_pixels (QgsVectorLayer): selected pixels from flow accumulation
    - filtered_px (Tuple[float, ...]): flow accumulation values filtered based on threshold

    Returns:
    Dict[float, QgsFeature]: distance as key and feature as value
    """
    distance_area = QgsDistanceArea()
    distance_area.setEllipsoid('WGS84')
    given_centroid = list(point_lyr.getFeatures())[0].geometry().centroid().asPoint()
    dist_dict = {}
    for f in selected_pixels.getFeatures():
        if f['elevation'] in filtered_px:
            centroid = f.geometry().centroid().asPoint()
            distance = distance_area.measureLine(given_centroid, centroid)
            dist_dict[distance] = f
    return dist_dict

def correct_point(point_lyr: QgsVectorLayer, flow_acc_path: str, buffer_distance: float, threshold: float) -> Tuple[float, float, str]:
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
    buffer_200 = create_buffer(point_lyr.source(), 0.0018018018) # 200m buffer
    print('buffer calculation completed.')
    mask_200_path = mask_dem(flow_acc_path, buffer_200)
    elev_poly = dem_polygonize(mask_200_path)
    selected_pixels = intersection_poly(elev_poly, structure_buffer)
    flow_px_list = [f['elevation'] for f in selected_pixels.getFeatures()]
    filtered_px, warning = check_threshold(threshold, flow_px_list)
    dist_dict = distance_feature_dict(point_lyr, selected_pixels, filtered_px)
    selected_feature = dist_dict[min(dist_dict.keys())]
    selected_centroid = selected_feature.geometry().centroid().asPoint()
    return selected_centroid.y(), selected_centroid.x(), warning

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

def feature_counts(lyr: QgsVectorLayer) -> int:
    count = lyr.featureCount()
    print(f'no. of ponding pixels: {count}')
    return count

def main(data: str, latitude, longitude, eff_heights) -> None:
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
    elif data == 'cartosat':
        dem = cartosat
        flow_acc = cartosat_flow_acc
        drain_dir = cartosat_drain_dir
        px_size = cartosat_px
        buffer = cartosat_buffer
        threshold = cartosat_flow_acc_threshold
    else:
        raise ValueError('mention the dataset used!')
    print(f'\n# {data} calculation:')
    label = f'{latitude}_{longitude}'.replace('.','-')
    map(check_projection, (dem, flow_acc, drain_dir))
    given_pt = point_layer(latitude, longitude, f'given_point_{label}')
    lat, long, warning = correct_point(given_pt, flow_acc, buffer, threshold)
    pt_lyr = point_layer(lat, long, f'calculated_point_{label}')
    catchment_raster_path = catchment_delineation(lat, long, drain_dir)
    catchment_poly_path = catchment_polygonize(catchment_raster_path, f'catchment_polygonized_{label}')
    masked_elev_path = mask_dem(dem, catchment_poly_path)
    # processing2lyr(masked_elev_path, 'elevation_masked')
    print('masking elevation to catchment completed.')
    lowest_elev = low_elev_point(pt_lyr, masked_elev_path)
    elev_lyr = dem_polygonize(masked_elev_path)
    print('polygonizing masked elevation completed.')
    if not isinstance(eff_heights, Iterable):
        eff_heights = (eff_heights,)
    for eff_height in eff_heights:
        eff_label = f'{eff_height}_{latitude}_{longitude}'.replace('.','-')
        print(f'processing: {eff_label}')
        elev_lyr = calc_depth(lowest_elev, eff_height, elev_lyr, f'elevation_polygonized_{eff_label}')
        pond_lyr = pond_pixels(elev_lyr, eff_height, f'pond_pixels_{eff_label}')
        count = feature_counts(pond_lyr)
        area = count * px_size * px_size
        volume = calc_volume(pond_lyr, px_size, eff_label)
        outdict[eff_label]={
            f'Num_{data}': count,
            # f'Pond_Area_m2_{data}': area,
            f'Vol_{data}': volume
        }
        if warning: print(f'# {warning}')

print('started...')
for dataset, latitude, longitude, eff_heights in inputs:
    main(dataset, latitude, longitude, eff_heights)
df = pd.DataFrame(outdict).T
print(df)
print('completed!!!')
