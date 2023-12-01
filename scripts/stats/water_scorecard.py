import json
from typing import Tuple, Optional, Any

import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
import pandas as pd
from qgis.core import QgsJsonExporter
from qgis.utils import iface

#input
YEAR = 2019
persons_per_hh = 4
lpcd = 55
NDVI_THRESHOLD = 0.2
BACKLOG_YEARS = 5

def season_dict(year):
    return {
        'kharif_start' : f'{year}-06-01', # June of YEAR
        'kharif_end' : f'{year}-10-01', # September of YEAR
        'rabi_start' : f'{year}-10-01', # October of YEAR
        'rabi_end' : f'{year+1}-02-01', # January of YEAR+1
        'zaid_start' : f'{year+1}-02-01', # February of YEAR+1
        'zaid_end' : f'{year+1}-06-01', # May of YEAR+1
    }

def year_range(year, no_of_years):
    return list(range(year,year-no_of_years,-1))

# Initialize Earth Engine
ee.Initialize()

# GEE Collections
microsoftBuildingsCol = ee.FeatureCollection('projects/sat-io/open-datasets/MSBuildings/India')
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
DW_CROP_LABEL = 4

def lyr2ee(active_lyr):
    print(f'Active Layer: {active_lyr.name()}')
    def convert2ee(active_lyr, features):
        lyr = QgsJsonExporter(active_lyr)
        gs = lyr.exportFeatures(features)
        gj = json.loads(gs)
        for feature in gj["features"]:
            feature["id"] = f'{feature["id"]:04d}'
        print('feature converted to EE object.')
        return ee.FeatureCollection(gj)
    selected_count = active_lyr.selectedFeatureCount()
    if selected_count > 0:
        print(f'selected features: {selected_count}')
        return convert2ee(active_lyr, active_lyr.selectedFeatures())
    else:
        return convert2ee(active_lyr, active_lyr.getFeatures())

def fc_area(roi):
    area = ee.Number(roi.geometry().area()).getInfo()
    areaSqKm = area/1e6
    print(f'area of ROI: {round(areaSqKm, 2)} Km2')
    return area, areaSqKm

def dataframe_generation(**kwargs):
    df = pd.DataFrame(kwargs)
    print(df.round(2))

def M_building_count(roi):
    buildings = microsoftBuildingsCol.filter(ee.Filter.bounds(roi.geometry()))
    m_count = int(buildings.size().getInfo())
    print(f'Building count from Microsoft: {m_count}')
    return m_count

def G_building_count(roi):
    buildings = googleBuildingsCol.filter('confidence >= 0.75').filter(ee.Filter.bounds(roi.geometry()))
    g_count = int(buildings.size().getInfo())
    print(f'Building count from Google: {g_count}')
    return g_count

def hh_requirement(roi):
    hh_count = max(M_building_count(roi), G_building_count(roi))
    print(f'no. of buildings in the ROI: {hh_count}')
    print(f'no. of person in a household: {persons_per_hh}')
    print(f'considering LPCD of {lpcd} litres')
    water = round(lpcd * 0.001 * 365, 2)
    print(f'amount of water per person per year is {water} cubic meters')
    domestic_m3 = hh_count * persons_per_hh * water
    domestic_mcm = domestic_m3/1e6
    # print(f'Domestic HH requirement: {round(domestic_m3,2)} cubic meters')
    print(f'Domestic HH requirement: {round(domestic_mcm,2)} MCM')
    return domestic_m3, domestic_mcm

def get_crop_mask(roi, crop_start, crop_end):
    dw = dwCol.filterDate(crop_start, crop_end).filterBounds(roi).select(['label']).mode()
    return dw.eq(DW_CROP_LABEL).selfMask()

def get_masked_ndvi_m2(start_date, end_date, roi, crop_mask):
    ndvi = l8.filterDate(start_date, end_date).filterBounds(roi).map(lambda x:x.normalizedDifference(['B5','B4']).rename('NDVI')).median()
    veg_mask = ndvi.gte(NDVI_THRESHOLD).updateMask(crop_mask)
    area_image = veg_mask.multiply(ee.Image.pixelArea())
    area = area_image.reduceRegion(reducer=ee.Reducer.sum(
    ), geometry=roi, scale=30, maxPixels=1e10)
    return ee.Number(area.get('NDVI')).getInfo()

def irrigation_area(year, roi):
    return {yr: get_masked_ndvi_m2(
        season_dict(yr)['rabi_start'],
        season_dict(yr)['rabi_end'], 
        roi, 
        get_crop_mask(roi, season_dict(yr)['kharif_start'], season_dict(yr)['zaid_end'])
        ) for yr in year_range(year, BACKLOG_YEARS)}

def get_crop_m2(roi, crop_start, crop_end):
    crop_mask = get_crop_mask(roi, crop_start, crop_end)
    area_image = crop_mask.multiply(ee.Image.pixelArea())
    area = area_image.reduceRegion(reducer=ee.Reducer.sum(
    ), geometry=roi, scale=10, maxPixels=1e10)
    return ee.Number(area.get('label')).getInfo()

def crop_area(year, roi):
    return {yr: get_crop_m2(
        roi,
        season_dict(yr)['kharif_start'],
        season_dict(yr)['zaid_end']
        ) for yr in year_range(year, BACKLOG_YEARS)}

def access_indicator(year, irr_dict, crop_dict):
    return {yr: (irr_dict[yr]/crop_dict[yr]) for yr in year_range(year, BACKLOG_YEARS)}

def resilience_indicator(area_dict):
    min_val = min(area_dict.values())
    print(f'min area: {round(min_val,2)}')
    max_val = max(area_dict.values())
    print(f'max area: {round(max_val,2)}')
    return min_val/max_val

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
            scale=100,
            maxPixels=1e10
        ).getInfo()['b1']
    return ETo_dict

def main(year):
    # Boundary will be automatically fetched from the QGIS active layer
    active_lyr = iface.activeLayer()
    roi = lyr2ee(active_lyr)
    geo_m2, geo_km2 = fc_area(roi)
    print(f'input year: {year}')
    
    # Access Indicator
    irr_dict = irrigation_area(year, roi)
    crop_dict = crop_area(year, roi)
    access_dict = access_indicator(year, irr_dict, crop_dict)
    dataframe_generation(irrigation_m2=irr_dict,cropland_m2=crop_dict,access_indicator=access_dict)
    print(f'Access Indicator (5yr mean): {round(sum(access_dict.values())/len(access_dict.values()),2)}')
    
    # Resilience Indicator
    print(f'crop reselience indicator: {round(resilience_indicator(crop_dict),2)}')
    print(f'irrigation reselience indicator: {round(resilience_indicator(irr_dict),2)}')
    
    #Availability Indicator
    domestic_m3, domestic_mcm = hh_requirement(roi)

main(YEAR)
