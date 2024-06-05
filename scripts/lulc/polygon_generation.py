from qgis.utils import iface
from qgis._core import QgsFeatureIterator
from qgis.core import QgsProject, QgsVectorLayer, QgsVectorFileWriter
from qgis import processing
import os
import tempfile

folder_path = r"C:\Users\atree\Desktop\QC_polygons"
village_field = 'village_na'

def selected_features():
    active_lyr = iface.activeLayer()
    lyr_name = active_lyr.name()
    print(f'Active Layer: {lyr_name}')
    selected_count = active_lyr.selectedFeatureCount()
    if selected_count > 0:
        print(f'selected features: {selected_count}')
        return active_lyr.selectedFeatures()
    else:
        print('Selected all features in layer')
        return active_lyr.getFeatures()

def create_layer(feature, lyr_name, filepath):
    layer = QgsVectorLayer('Polygon?crs=EPSG:4326', lyr_name, 'memory')
    pr = layer.dataProvider()
    pr.addFeature(feature)
    layer.updateExtents()
    # QgsProject.instance().addMapLayer(layer)
    save_options = QgsVectorFileWriter.SaveVectorOptions()
    save_options.driverName = "ESRI Shapefile"
    save_options.fileEncoding = "UTF-8"
    transform_context = QgsProject.instance().transformContext()
    file_write = QgsVectorFileWriter.writeAsVectorFormatV3(layer,
                                                    filepath,
                                                    transform_context,
                                                    save_options)
    if file_write[0] == QgsVectorFileWriter.NoError:
        print("success in creating shapefile")
    else:
        raise FileNotFoundError('Shapefile creating failed')
    return layer, file_write

def create_buffer(input_layer, buffer_distance):
    params = {
        'INPUT':input_layer,
        'DISTANCE':buffer_distance,
        'SEGMENTS':8,
        'END_CAP_STYLE':0,
        'JOIN_STYLE':0,
        'MITER_LIMIT':2,
        'DISSOLVE':False,
        'OUTPUT':'TEMPORARY_OUTPUT'
    }
    result = processing.run("native:buffer", params)
    return result['OUTPUT']

def create_points(vector_lyr):
    params = {
        'INPUT': vector_lyr,
        'STRATEGY': 0,
        'VALUE': 30,
        'MIN_DISTANCE': 250/111000,
        'OUTPUT':'TEMPORARY_OUTPUT'
    }
    result = processing.run("qgis:randompointsinsidepolygons", params)
    return result['OUTPUT']

def create_polygons(pt_lyr, filepath):
    params = {
        'INPUT': pt_lyr,
        'SHAPE': 0,
        'WIDTH': 100/111000,
        'HEIGHT': 100/111000,
        'ROTATION': None,
        'SEGMENTS': 4,
        'OUTPUT': filepath
    }
    result = processing.run("native:rectanglesovalsdiamonds", params)
    return result['OUTPUT']

def main():
    try:
        create_temp_dir = tempfile.TemporaryDirectory()
        temp_dir = create_temp_dir.name
        features = selected_features()
        if isinstance(features, QgsFeatureIterator):
            raise AttributeError('select one feature from the layer')
        feature = features[0]
        village_name = feature[village_field]
        print(f'selected: {village_name}')
        temp_file = os.path.join(temp_dir, f'temp_{village_name}_vector.shp')
        village_layer, file_written = create_layer(feature, f'remove_{village_name}', temp_file)
        print(f'created layer for the {village_name} boundary')
        buff_dist = -70/111000
        # buffer = create_buffer(village_layer.source(), buff_dist)
        buffer = create_buffer(temp_file, buff_dist)
        print('Created buffer for the village boundary')
        random_pts = create_points(buffer)
        print('created random points inside the village')
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f'Folder Not Found: {folder_path}')
        filepath = os.path.join(folder_path, f'{village_name}_polygons.shp')
        _ = create_polygons(random_pts, filepath)
        print('created polygons inside the village')
        create_temp_dir.cleanup()
    except Exception as e:
        print(e)
        print('ignore the error!')
    print('completed!!!')

main()