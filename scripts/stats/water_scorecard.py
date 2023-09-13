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

def fc_area(roi):
    area = ee.Number(roi.geometry().area()).getInfo()
    areaSqKm = round(area/1e6)
    print(f'area of ROI: {round(area, 2)} m2')
    return area, areaSqKm

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
    domestic_m3 = hh_count * persons * water
    return round(domestic_m3, 3), round(domestic_m3/1e6, 3)

def get_rainfall(start_date, end_date, roi):
    sum_image = imdrain.filterDate(start_date, end_date).sum()
    return sum_image.reduceRegion(ee.Reducer.mean(),roi,100).getInfo()['b1']

def renewable_water_req(start_date, end_date, roi):
    rain_mm = get_rainfall(start_date, end_date, roi)
    print(f'rainfall in mm: {round(rain_mm,2)}')
    cgwb_coeff = 0.2
    print(f'considering CGWB coefficient as {cgwb_coeff*100}%')
    renewable_mm = cgwb_coeff * rain_mm
    area_m2, _ = fc_area(roi)
    renewable_m3 = area_m2*(renewable_mm/1000)
    return round(renewable_mm, 2), round(renewable_m3, 3), round(renewable_m3/1e6, 3)

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
    domestic_m3, domestic_mcm = hh_requirement(roi)
    print(f'Domestic HH requirement: {domestic_m3} cubic meters')
    print(f'-> Domestic HH requirement: {domestic_mcm} MCM')
    renewable_mm, renewable_m3, renewable_mcm = renewable_water_req(start_date, end_date, roi)
    print(f'Renewable water by CGWB is {renewable_mm} mm')
    print(f'Renewable water by CGWB is {renewable_m3} cubic meters')
    print(f'-> Renewable water by CGWB is {renewable_mcm} MCM')

main(2021)
