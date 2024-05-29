import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface
import json

# Inputs
year = 2019

# constants
start_date = f"{year}-12-31"
end_date = f"{year+1}-01-31"

# Initialize Earth Engine
ee.Initialize()

S2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")

def lyr2ee(active_lyr):
    # Boundary will be automatically fetched from the QGIS active layer
    def convert2ee(active_lyr, features):
        lyr = QgsJsonExporter(active_lyr)
        gs = lyr.exportFeatures(features)
        gj = json.loads(gs)
        for feature in gj["features"]:
            feature["id"] = f'{feature["id"]:04d}'
        return ee.FeatureCollection(gj)
    selected_count = active_lyr.selectedFeatureCount()
    if selected_count > 0:
        print(f'selected features: {selected_count}')
        return convert2ee(active_lyr, active_lyr.selectedFeatures())
    else:
        return convert2ee(active_lyr, active_lyr.getFeatures())

def s2_image(roi, start_date, end_date):
    return (
        S2.filterDate(start_date, end_date)\
        .filterBounds(roi.geometry())\
        .sort('CLOUDY_PIXEL_PERCENTAGE', False)\
        .select(['B4', 'B3', 'B2'])\
        .mosaic()\
        .clip(roi)
    )

def map_s2(image):
    Map.addLayer(image,
                {'min': 0, 'max': 4500, 'gamma':1, 'bands': ['B4', 'B3', 'B2']},
                f'S2-{year}')

def ndvi_image(roi, start_date, end_date):
    image = S2.filterDate(start_date, end_date)\
        .filterBounds(roi.geometry())\
        .filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 10))\
        .select(['B8', 'B4', 'B3'])\
        .qualityMosaic('B3')\
        .clip(roi)
    return image.normalizedDifference(['B8', 'B4'])

def map_ndvi(image):
    Map.addLayer(image,
                {'min': 0, 'max': 0.6, 'palette':['red','yellow','green']},
                f'ndvi-{year}')

def main():
    active_lyr = iface.activeLayer()
    lyr_name = active_lyr.name()
    print(f'Active Layer: {lyr_name}')
    roi = lyr2ee(active_lyr)
    print('getting Sentinel image')
    sat_image = s2_image(roi, start_date, end_date)
    print('adding sentinel image to the QGIS workspace')
    map_s2(sat_image)
    print('getting ndvi image')
    ndvi = ndvi_image(roi, start_date, end_date)
    print('adding ndvi image to the QGIS workspace')
    map_ndvi(ndvi)
    print('completed!!!')

main()
