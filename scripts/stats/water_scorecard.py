import json
from typing import Tuple, Optional, Any

import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface

#input
YEAR = 2019

# Initialize Earth Engine
ee.Initialize()

# GEE Collections
buildingsCol = ee.FeatureCollection('projects/sat-io/open-datasets/MSBuildings/India')
googleBuildingsCol = ee.FeatureCollection('GOOGLE/Research/open-buildings/v3/polygons')
imdrain = ee.ImageCollection('users/jaltolwelllabs/IMD/rain')
EToCol = ee.ImageCollection('users/jaltolwelllabs/ET/refCropET')
dwCol = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
ndviCol = ee.ImageCollection("MODIS/061/MOD13Q1")
l8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA")
if YEAR >= 2021:
    modisET = ee.ImageCollection("MODIS/061/MOD16A2")
else:
    modisET = ee.ImageCollection("MODIS/006/MOD16A2")

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
    areaSqKm = round(area/1e6, 2)
    return area, areaSqKm

def building_count(roi):
    buildings = buildingsCol.filter(ee.Filter.bounds(roi.geometry()))
    return buildings.size().getInfo()

def G_building_count(roi):
    buildings = googleBuildingsCol.filter('confidence >= 0.75').filter(ee.Filter.bounds(roi.geometry()))
    return buildings.size().getInfo()

def hh_requirement(roi, hh_col):
    if hh_col == 'Microsoft':
        hh_count = building_count(roi)
    elif hh_col == 'Google':
        hh_count = G_building_count(roi)
    else:
        hh_count = 0
    print(f'no. of buildings in the ROI ({hh_col}): {hh_count}')
    
    persons = 4
    print(f'no. of person in a household: {persons}')
    lpcd = 55
    print(f'considering LPCD of {lpcd} litres')
    water = round(lpcd * 0.05 * 365, 2)
    print(f'amount of water per person per year is {water} cubic meters')
    domestic_m3 = hh_count * persons * water
    return round(domestic_m3, 3), round(domestic_m3/1e6, 3)

def get_rainfall(start_date, end_date, roi):
    sum_image = imdrain.filterDate(start_date, end_date).sum()
    return sum_image.reduceRegion(ee.Reducer.mean(),roi,100).getInfo()['b1']

def get_ET(start_date, end_date, roi):
    dw = dwCol.filterDate(start_date, end_date).filterBounds(roi).select(['label']).mode()
    et = modisET.filterDate(start_date, end_date).select(['ET']).filterBounds(roi).sum()
    crop_et = et.updateMask(dw.eq(4))
    return crop_et.reduceRegion(ee.Reducer.mean(),roi,500).getInfo()['ET']

def recharge(start_date, end_date, roi, roi_area_m2):
    rain_mm = get_rainfall(start_date, end_date, roi)
    print(f'rainfall in mm: {round(rain_mm,2)}')
    cgwb_coeff = 0.07
    print(f'considering CGWB coefficient as (Wheathered Basalt) {cgwb_coeff*100}%')
    recharge_mm = cgwb_coeff * rain_mm
    recharge_m3 = roi_area_m2*(recharge_mm/1000)
    return round(recharge_mm, 2), round(recharge_m3, 3), round(recharge_m3/1e6, 3)

def mo_yr_seq(year):
    monthseq = list(range(6, 13)) + list(range(1, 6))
    yearseq = [year]*7 + [year+1]*5
    return [*zip(yearseq, monthseq)]

def get_refET(geometry, year):
    ETo_dict = {}  # {month: ETo}
    monthyearseq = mo_yr_seq(year)
    for period in monthyearseq:
        y, m = period
        image = EToCol.filterDate(ee.Date.fromYMD(
            y, m, 1).getRange('month')).first()
        ETo_dict[f'{m:02d}'] = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=30,
            maxPixels=1e10
        ).getInfo()['b1']
    return ETo_dict

def get_crop_area(start_date, end_date, label, geometry):
    dw = dwCol.filterDate(start_date, end_date).filterBounds(geometry).select(['label']).mode()
    label_mask = dw.eq(label).selfMask()
    area_image = label_mask.multiply(ee.Image.pixelArea())
    area = area_image.reduceRegion(reducer=ee.Reducer.sum(
    ), geometry=geometry, scale=10, maxPixels=1e10)
    return label_mask, ee.Number(area.get('label')).getInfo()

def get_ndvi(start_date, end_date, roi, crop_mask):
    # ndvi = ndviCol.filterDate(start_date, end_date).filterBounds(roi).select(['NDVI']).median()
    # veg_mask = ndvi.gte(2000).updateMask(crop_mask)
    ndvi = l8.filterDate(start_date, end_date).filterBounds(roi).map(lambda x:x.normalizedDifference(['B5','B4']).rename('NDVI')).median()
    veg_mask = ndvi.gte(0.2).updateMask(crop_mask)
    area_image = veg_mask.multiply(ee.Image.pixelArea())
    area = area_image.reduceRegion(reducer=ee.Reducer.sum(
    ), geometry=roi, scale=10, maxPixels=1e10)
    return veg_mask, ee.Number(area.get('NDVI')).getInfo()

def get_access(year, roi, crop_m2, crop_mask):
    irr_start = f'{year}-10-01'
    irr_end = f'{year+1}-02-01'
    irr_mask, irr_m2 = get_ndvi(irr_start, irr_end, roi, crop_mask)
    print(f'Irrigation area {year}: {irr_m2} m2')
    khar_start = f'{year}-06-01'
    khar_end = f'{year}-10-01'
    _, khar_m2 = get_ndvi(khar_start, khar_end, roi, crop_mask)
    print(f'Kharif Crop area (NDVI) {year}: {khar_m2} m2')
    zaid_start = f'{year+1}-02-01'
    zaid_end = f'{year+1}-06-01'
    _, zaid_m2 = get_ndvi(zaid_start, zaid_end, roi, crop_mask)
    print(f'Zaid Crop area (NDVI) {year}: {zaid_m2} m2')
    return irr_m2/crop_m2

def get_resilience(year, roi):
    def cal_irr(year):
        irr_start = f'{year}-10-01'
        irr_end = f'{year+1}-02-01'
        crop_start = f'{year}-06-01'
        crop_end = f'{year+1}-06-01'
        dw = dwCol.filterDate(crop_start, crop_end).filterBounds(roi).select(['label']).mode()
        crop_mask = dw.eq(4).selfMask()
        _, irr_m2 = get_ndvi(irr_start, irr_end, roi, crop_mask)
        print(f'irr_area - {year}: {irr_m2}')
        return irr_m2
    def cal_crop(year):
        crop_start = f'{year}-06-01'
        crop_end = f'{year+1}-06-01'
        dw = dwCol.filterDate(crop_start, crop_end).filterBounds(roi).select(['label']).mode()
        label_mask = dw.eq(4).selfMask()
        area_image = label_mask.multiply(ee.Image.pixelArea())
        area = area_image.reduceRegion(reducer=ee.Reducer.sum(
        ), geometry=roi, scale=10, maxPixels=1e10)
        area_val = ee.Number(area.get('label')).getInfo()
        print(f'Crop_area - {year}: {area_val}')
        return area_val
    crop_list = list(map(cal_crop, list(range(year, year-5, -1))))
    irr_list = list(map(cal_irr, list(range(year, year-5, -1))))
    min_crop = min(crop_list)
    max_crop = max(crop_list)
    min_irr = min(irr_list)
    max_irr = max(irr_list)
    print(f'min crop area: {min_crop}')
    print(f'max crop area: {max_crop}')
    print(f'min irrigated area: {min_irr}')
    print(f'max irrigated area: {max_irr}')
    crop_resilience = min_crop/max_crop
    irr_resilience = min_irr/max_irr
    return crop_resilience, irr_resilience

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
    
    geo_m2, geo_km2 = fc_area(roi)
    print(f'area of ROI: {round(geo_m2, 2)} m2')
    print(f'area of ROI: {round(geo_km2, 2)} Km2')
    print('ROI details: completed\n')
    
    domestic_m3, domestic_mcm = hh_requirement(roi, 'Google')
    print(f'Domestic HH requirement: {domestic_m3} cubic meters')
    print(f'-> Domestic HH requirement: {domestic_mcm} MCM')
    print('HH details: completed\n')
    
    ETodict = get_refET(roi, year)
    print(f'ET0 Dict for {year}:\n{ETodict}')
    crop_mask, crop_area_m2 = get_crop_area(start_date, end_date, 4, roi)
    print(f'crop area in ROI: {crop_area_m2} m2')
    print('CWR details: completed\n')
    
    et_mm = get_ET(start_date, end_date, roi)
    print(f'Modis Evapotranspiration: {et_mm} mm')
    recharge_mm, recharge_m3, recharge_mcm = recharge(start_date, end_date, roi, geo_m2)
    print(f'recharge water by CGWB is {recharge_mm} mm')
    print(f'recharge water by CGWB is {recharge_m3} cubic meters')
    print(f'-> recharge water by CGWB is {recharge_mcm} MCM')
    print('recharge details: completed\n')

    access = get_access(year, roi, crop_area_m2, crop_mask)
    print(f'Access indicator: {access}')
    print('Access Indicator: completed\n')

    crop_resilience, irr_resilience = get_resilience(year, roi)
    print(f'Crop Resilience: {crop_resilience}')
    print(f'Irrigation Resilience: {irr_resilience}')
    print('Resilience Indicator: completed')

    print('Completed!!!')

main(YEAR)
