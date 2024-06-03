import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface
import json

# Inputs
village_name = 'Oravoy'
gcp_project = 'gcp-welllabs'
export2drive = True
qgis_layer = False
year = 2019

# constants
start_date = f"{year}-12-31"
end_date = f"{year+1}-01-31"

# Initialize Earth Engine
ee.Initialize(project=gcp_project)

S2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
srtm = ee.Image("USGS/SRTMGL1_003")

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

def srtm_image(roi):
    return srtm.clip(roi)

def map_srtm(image, roi):
    min_val = image.reduceRegion(
            reducer=ee.Reducer.min(),
            geometry=roi.geometry(),
            scale=30,
            crs='EPSG:4326',
            maxPixels=1e11
        ).getInfo()['elevation']
    max_val = image.reduceRegion(
            reducer=ee.Reducer.max(),
            geometry=roi.geometry(),
            scale=30,
            crs='EPSG:4326',
            maxPixels=1e11
        ).getInfo()['elevation']
    Map.addLayer(image,
                {'min': min_val, 'max': max_val, 'palette':['red','yellow','blue']},
                'elevation-srtm')

def export_layer(image, roi, data):
    image_export_task = ee.batch.Export.image.toDrive(
        image = image,
        description = f'{village_name}_{data}_{year}',
        region = roi.geometry(),
        scale = 10,
        maxPixels = 1e13,
        crs = 'EPSG:4326'
    )

    image_export_task.start()
    return image_export_task

def main():
    active_lyr = iface.activeLayer()
    lyr_name = active_lyr.name()
    print(f'Active Layer: {lyr_name}')
    roi = lyr2ee(active_lyr)
    print('getting Sentinel image')
    sat_image = s2_image(roi, start_date, end_date)
    if qgis_layer:
        print('adding sentinel image to the QGIS workspace')
        map_s2(sat_image)
    if export2drive:
        print('sentinel image export to drive initiated')
        sat_task = export_layer(sat_image, roi, 'sentinel2')
    print('getting ndvi image')
    ndvi = ndvi_image(roi, start_date, end_date)
    if qgis_layer:
        print('adding ndvi image to the QGIS workspace')
        map_ndvi(ndvi)
    if export2drive:
        print('NDVI image export to drive initiated')
        ndvi_task = export_layer(ndvi, roi, 'NDVI')
    print('getting srtm image')
    elev = srtm_image(roi)
    if qgis_layer:
        print('adding srtm image to the QGIS workspace')
        map_srtm(elev, roi)
    if export2drive:
        print('srtm image export to drive initiated')
        elev_task = export_layer(elev, roi, 'SRTM')
    if export2drive:
        print(sat_task.status())
        print(ndvi_task.status())
        print(elev_task.status())
    print('completed!!!')

main()
