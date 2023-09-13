import json
from typing import Tuple, Optional, Any

import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface

# Initialize Earth Engine
ee.Initialize()

# GEE Collections
buildingsCol = ee.FeatureCollection('projects/sat-io/open-datasets/MSBuildings/India')
imdrain = ee.ImageCollection('users/jaltolwelllabs/IMD/rain')

def lyr2ee(active_lyr):
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

def building_count(roi):
    buildings = buildingsCol.filter(ee.Filter.bounds(roi.geometry()))
    return buildings.size().getInfo()

def hh_requirement(roi):
    hh_count = building_count(roi)
    print(f'no. of buildings in the ROI: {hh_count}')
    persons = 4
    print(f'no. of person in a household: {persons}')
    lpcd = 55
    print(f'considering LPCD of {lpcd} litres')
    water = round(55 * 0.05 * 365, 2)
    print(f'amount of water per person per year is {water} cubic meters')
    return round((hh_count * persons * water)/1e6, 3)

def get_rainfall(start_date, end_date, roi):
    sum_image = imdrain.filterDate(start_date, end_date).sum()
    return sum_image.reduceRegion(ee.Reducer.mean(),roi,100).getInfo()['b1']

def renewable_water_req(start_date, end_date, roi):
    rain_mm = get_rainfall(start_date, end_date, roi)
    print(f'rainfall in mm: {rain_mm}')
    cgwb_coeff = 0.2
    print(f'considering CGWB coefficient as {cgwb_coeff*100}%')
    return round(cgwb_coeff * rain_mm, 2)

def main(year):
    print(f'input year: {year}')
    start_date = f'{year}-06-01'
    end_date = f'{year+1}-06-01'
    print(f'start date: {start_date}, end date: {end_date}')
    # Boundary will be automatically fetched from the QGIS active layer
    active_lyr = iface.activeLayer()
    lyr_name = active_lyr.name()
    print(f'Active Layer: {lyr_name}')
    roi = lyr2ee(active_lyr)
    domestic_req = hh_requirement(roi)
    print(f'-> Domestic HH requirement: {domestic_req} MCM')
    renewable_water = renewable_water_req(start_date, end_date, roi)
    print(f'-> Renewable water by CGWB is {renewable_water} mm')

main(2021)
