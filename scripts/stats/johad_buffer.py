from functools import WRAPPER_ASSIGNMENTS
from PyQt5.QtCore import QVariant
from qgis import processing
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsRasterLayer, QgsDistanceArea, QgsCoordinateReferenceSystem, QgsField, QgsFeature, QgsPointXY, QgsGeometry, QgsProcessingUtils, QgsProcessingContext, QgsExpression, QgsVectorFileWriter, QgsCoordinateTransformContext
from typing import Tuple, List, Dict, Union
from pathlib import Path
import pandas as pd

lat_column = 'Latitude'
long_column = 'Longitude'
unique_column = 'Structure'
anicut_buffer = 250
pokher_buffer = 250
taal_buffer = 250
pokher_length = 300
taal_length = 1000

# config for data and location of required files
px = 30 # pixel size
buffer = 90/111000 # 90m
dem = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Elevation_FABDEM_Karauli.tif"
flow_acc = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Flow_Accumulation_FABDEM_Karauli.tif"
drain_dir = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Rasters\FABDEM\Drainage_Direction_FABDEM_Karauli.tif"
dem_poly = r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\Vectors\FABDEM_Karauli_3kmBuffer_poly.shp"
elev_poly = QgsVectorLayer(dem_poly, "dem polygon", "ogr")

vectors_path = Path(r'C:\Users\atree\Documents\WELL_Labs\jaltol\TBS\vectors')

# calc_pt_path.mkdir(parents=True, exist_ok=True)


def point_layer(latitude: float, longitude: float, lyr_name: str, unique_field) -> QgsVectorLayer:
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
    fields = [QgsField('Longitude', QVariant.Double), QgsField('Latitude', QVariant.Double), QgsField('name', QVariant.String)]
    pr.addAttributes(fields)
    layer.updateFields()
    feature = QgsFeature()
    feature.setGeometry(QgsGeometry.fromPointXY(point))
    feature.setAttributes([longitude, latitude, unique_field])
    pr.addFeature(feature)
    layer.updateExtents()
    QgsProject.instance().addMapLayer(layer)
    print('point layer added.')
    return layer, feature

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
    buffer_200 = create_buffer(point_lyr.source(), 200/111000) # 200m buffer
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

def get_drainage_line(point_lyr, flow_acc_path, length, name):
    starting_point = point_lyr.source()
    structure_buffer = create_buffer(starting_point, (length+30)/111000)
    # mask_path = mask_dem(flow_acc_path, structure_buffer)
    # elev_poly = dem_polygonize(mask_path)
    threshold = 0
    threshold_list = [0]
    points_list = [list(point_lyr.getFeatures())[0].geometry().centroid().asPoint()]
    for _ in range(int(length/30)):
        buffer_25 = create_buffer(starting_point, 25/111000) # buffer for nearby points
        selected_pixels = intersection_poly(elev_poly, buffer_25)
        flow_px_list = [f['elevation'] for f in selected_pixels.getFeatures()]
        # filtered_px, warning = check_threshold(threshold, flow_px_list)
        # flow_px_list= tuple(filter(lambda x: x>=threshold, flow_px_list))
        flow_px_list= tuple(filter(lambda x: x not in threshold_list, flow_px_list))
        max_flow = min(flow_px_list)
        for f in selected_pixels.getFeatures():
            if f['elevation'] == max_flow:
                centroid = f.geometry().centroid().asPoint()
                points_list.append(centroid)
                starting_point, _ = point_layer(centroid.y(), centroid.x(), 'intermediate_pt', name)
        threshold = max_flow
        threshold_list.append(max_flow)
    geom = QgsGeometry.fromPolylineXY(points_list)
    layer = QgsVectorLayer('LineString?crs=EPSG:4326', 'drainage_line', 'memory')
    pr = layer.dataProvider()
    fields = [QgsField('name', QVariant.String)]
    pr.addAttributes(fields)
    layer.updateFields()
    feature = QgsFeature()
    feature.setGeometry(geom)
    feature.setAttributes([name])
    pr.addFeature(feature)
    layer.updateExtents()
    QgsProject.instance().addMapLayer(layer)
    print('polyline layer added.')
    return layer, feature

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

def main(structure, csvpath):
    csv = pd.read_csv(csvpath)
    given_pt_list = []
    calc_pt_list = []
    buffer_list = []
    warning_list = []
    line_list = []
    catchment_list = []
    for row in csv.iterrows():
        df = row[1]
        latitude = df[lat_column]
        longitude = df[long_column]
        unique_field = df[unique_column]
        given_pt, given_feat = point_layer(latitude, longitude, 'given_point',unique_field)
        given_pt_list.append(given_feat)
        lat, long, warning = correct_point(given_pt, flow_acc, buffer, 20)
        warning_list.append((unique_field, warning))
        pt_lyr, calc_feat = point_layer(lat, long, 'calculated_point', unique_field)
        calc_pt_list.append(calc_feat)
        if structure == 'anicut':
            structure_buffer = create_buffer(pt_lyr.source(), anicut_buffer/111000)
        elif structure == 'pokher':
            line_lyr, line_feat = get_drainage_line(pt_lyr, dem, pokher_length, unique_field)
            line_list.append(line_feat)
            structure_buffer = create_buffer(line_lyr.source(), pokher_buffer/111000)
        elif structure == 'taal':
            line_lyr, line_feat = get_drainage_line(pt_lyr, dem, taal_length, unique_field)
            line_list.append(line_feat)
            structure_buffer = create_buffer(line_lyr.source(), taal_buffer/111000)
        else:
            raise AttributeError('structure type is not found')
        QgsProject.instance().addMapLayer(structure_buffer)
        buffer_list.extend(iter(structure_buffer.getFeatures())) # append QgsFeatures to list
        catchment_raster_path = catchment_delineation(lat, long, drain_dir)
        catchment_poly_path = catchment_polygonize(catchment_raster_path)
        catchment_poly = QgsVectorLayer(catchment_poly_path, f"{unique_field}_catchment", "ogr")
        catchment_poly.startEditing()
        if catchment_poly.dataProvider().fieldNameIndex("name") == -1:
            catchment_poly.dataProvider().addAttributes([QgsField("name", QVariant.String)])
            catchment_poly.updateFields()
        id_new_col= catchment_poly.dataProvider().fieldNameIndex("name")
        for feature in catchment_poly.getFeatures():
            catchment_poly.changeAttributeValue(feature.id(), id_new_col, unique_field)
        catchment_poly.commitChanges()
        catchment_list.extend(iter(catchment_poly.getFeatures()))
    pt_fields = [QgsField('Longitude', QVariant.Double), QgsField('Latitude', QVariant.Double), QgsField('name', QVariant.String)]
    line_fields = [QgsField('name', QVariant.String)]
    catch_fields = [QgsField('fid',QVariant.Int), QgsField('val',QVariant.Int), QgsField('name', QVariant.String)]
    total_layers = [
            ('combined_given_pt',"Point?crs=EPSG:4326",given_pt_list,pt_fields),
            ('combined_calc_pt',"Point?crs=EPSG:4326",calc_pt_list,pt_fields),
            ('combined_buffer',"Polygon?crs=EPSG:4326",buffer_list,line_fields),
            ('combined_catchment',"Polygon?crs=EPSG:4326",catchment_list,catch_fields),
    ]
    if line_list: total_layers.append(('combined_drainage_lines','LineString?crs=EPSG:4326',line_list,line_fields))
    for name, path, feat_list, fields in total_layers:
        layer = QgsVectorLayer(path, name, "memory")
        pr = layer.dataProvider()
        pr.addAttributes(fields)
        layer.updateFields()
        pr.addFeatures(feat_list)
        layer.updateExtents()
        QgsProject.instance().addMapLayer(layer)

        # final_file = str(vectors_path.joinpath(f'{name}.shp'))
        # svOptions = QgsVectorFileWriter.SaveVectorOptions()
        # svOptions.driverName = "ESRI Shapefile"
        # svOptions.fileEncoding = "utf-8"
        # svOptions.onlySelectedFeatures = True
        # QgsVectorFileWriter.writeAsVectorFormatV2(layer, final_file, QgsCoordinateTransformContext(), svOptions)
    if warning_list:
        for name, msg in warning_list: 
            if msg: print(f'{name}:{msg}')
    print('Completed!!!')


# main('anicut', r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\CSVs\anicut_pokher_taal_karauli\Anicut_12Mar24.csv")
# main('pokher', r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\CSVs\anicut_pokher_taal_karauli\Pokher_12Mar24.csv")
main('taal', r"G:\Shared drives\Jaltol\Engagement\TBS\Ishita - Analysis + Data\GIS_files\Johad_Structures\CSVs\anicut_pokher_taal_karauli\Taal_12Mar24.csv")
