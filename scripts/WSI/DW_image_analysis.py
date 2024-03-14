import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface
import json

# Initialize Earth Engine
ee.Initialize()
DW = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
S2 = ee.ImageCollection("COPERNICUS/S2")

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

def DW_image(start_date, end_date, roi):
    return (
        DW.filterDate(start_date, end_date)
        .filterBounds(roi.geometry())
        .select("label")
        .mode()
        .clip(roi)
    )

def S2_image(date, roi):
    ee_date = ee.Date(date)
    start_date = ee_date.advance(-15, 'day')
    end_date = ee_date.advance(15, 'day')
    return (
        S2.filterDate(start_date, end_date)
        .filterBounds(roi.geometry())
        .filterMetadata('CLOUDY_PIXEL_PERCENTAGE', 'less_than', 40)
        .select(['B4', 'B3', 'B2'])
        .median()
        .clip(roi)
    )

def map_DW(image,start,end,label):
    viz = ["419bdf","397d49","88b053","7a87c6","e49635","dfc35a","c4281b","a59b8f","b39fe1"]
    Map.addLayer(image, {"palette": viz, "min": 0, "max": 8}, f"{label}-{start}-{end}")

def map_S2(image, date):
    Map.addLayer(image,
                {'min': 0, 'max': 4500, 'gamma':0.7, 'bands': ['B4', 'B3', 'B2']},
                f'S2-{date}')

def main(crop_start, crop_end, irr_start, irr_end, s2_list):
    active_lyr = iface.activeLayer()
    lyr_name = active_lyr.name()
    print(f'Active Layer: {lyr_name}')
    roi = lyr2ee(active_lyr)
    print(f'getting image for {crop_start} to {crop_end}')
    crop_image = DW_image(crop_start, crop_end, roi)
    print(f'getting image for {irr_start} to {irr_end}')
    irr_image = DW_image(irr_start, irr_end, roi)
    print('adding DW images to QGIS workspace')
    map_DW(crop_image, crop_start, crop_end, 'crop')
    map_DW(irr_image, irr_start, irr_end, 'irrig')
    for s2_date in s2_list:
        print(f'getting S2 image for {s2_date}')
        s2_im = S2_image(s2_date, roi)
        print(f'adding S2 map for {s2_date} to QGIS workspace')
        map_S2(s2_im, s2_date)
    print('completed!!!')

main('2022-06-01','2023-05-31','2022-10-01','2023-01-31',['2022-12-15'])