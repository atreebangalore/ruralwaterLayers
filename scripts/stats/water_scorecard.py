from calendar import monthrange
from datetime import datetime
from datetime import timedelta as td
import json
from typing import Tuple, Optional, Any, List, Dict

import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
import pandas as pd
from qgis.core import QgsJsonExporter
from qgis.utils import iface

#input
YEAR = 2019
KHARIF_START_MONTH = 6
RABI_START_MONTH = 10
ZAID_START_MONTH = 2
persons_per_hh = 4
lpcd = 55
NDVI_THRESHOLD = 0.2
BACKLOG_YEARS = 5
neglected_crops = ['Sugarcane']
CROPS_CONSIDERED = 5

# Initialize Earth Engine
ee.Initialize()

DIST_URL = 'https://raw.githubusercontent.com/atreebangalore/ruralwaterLayers/master/scripts/stats/scorecard_data/crop_area_literature.csv'
COEFF_URL = 'https://raw.githubusercontent.com/atreebangalore/ruralwaterLayers/master/scripts/stats/scorecard_data/crop_coefficient_FAO_chapter6.csv'

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

def season_dict(year):
    return {
        'kharif_start' : f'{year}-{KHARIF_START_MONTH:02d}-01', # June of YEAR
        'kharif_end' : f'{year}-{RABI_START_MONTH:02d}-01', # September of YEAR
        'rabi_start' : f'{year}-{RABI_START_MONTH:02d}-01', # October of YEAR
        'rabi_end' : f'{year+1}-{ZAID_START_MONTH:02d}-01', # January of YEAR+1
        'zaid_start' : f'{year+1}-{ZAID_START_MONTH:02d}-01', # February of YEAR+1
        'zaid_end' : f'{year+1}-{KHARIF_START_MONTH:02d}-01', # May of YEAR+1
    }

def year_range(year, no_of_years):
    return list(range(year,year-no_of_years,-1))

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

def read_url(url):
    return pd.read_csv(url)

def filter_df(df, dist, season):
    fil = df[(df['SOI_District']==dist) & (df['Season']==season) & (df['Percentage_Area']!=0)]
    return fil.copy().reset_index(drop=True)

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
    print(f'Domestic HH requirement: {round(domestic_m3,2)} cubic meters')
    # print(f'Domestic HH requirement: {round(domestic_mcm,2)} MCM')
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
    monthseq = list(range(KHARIF_START_MONTH, 13)) + list(range(1, KHARIF_START_MONTH))
    yearseq = [year]*(13-KHARIF_START_MONTH) + [year+1]*(KHARIF_START_MONTH-1)
    return [*zip(yearseq, monthseq)]

def no_of_days(year):
    seq = mo_yr_seq(year)
    mr_dict = {}
    for ele in seq:
        yr, mo = ele
        _, days = monthrange(yr, mo)
        mr_dict[f"{mo:02d}"] = days
    return mr_dict  # {month: no_of_days}

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

def get_ET(start_date, end_date, roi):
    dw = dwCol.filterDate(start_date, end_date).filterBounds(roi).select(['label']).mode()
    et = modisET.filterDate(start_date, end_date).select(['ET']).filterBounds(roi).sum()
    crop_et_mask = et.updateMask(dw.eq(4))
    crop_et = crop_et_mask.reduceRegion(ee.Reducer.mean(),roi,500).getInfo()['ET']
    print(f'MODIS crop ET (mm): {crop_et}')
    return crop_et

def get_rainfall(roi, year):
    P_dict = {}  # {month: ETo}
    monthyearseq = mo_yr_seq(year)
    for period in monthyearseq:
        y, m = period
        image = imdrain.filterDate(ee.Date.fromYMD(
            y, m, 1).getRange('month')).sum()
        P_dict[f'{m:02d}'] = image.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=roi,
            scale=1000,
            maxPixels=1e10
        ).getInfo()['b1']
    return P_dict

def check_area(area_m2, k):
    if isinstance(area_m2, float):
        return area_m2
    k = int(k)
    if k < RABI_START_MONTH and k>= KHARIF_START_MONTH:
        return area_m2['kharif']
    elif k < KHARIF_START_MONTH and k>= ZAID_START_MONTH:
        return area_m2['zaid']
    else:
        return area_m2['rabi']

def get_eff_rainfall_m3(area_m2, rain_mm_dict):
    rain_dict_mm = rain_mm_dict.copy()
    rain_dict_m3 = {}
    for k,v in rain_dict_mm.items():
        if v>75:
            rain_dict_mm[k] = ((0.8*v) - 25)
            rain_dict_m3[k] = (((0.8*v) - 25)/1000) * check_area(area_m2,k)
        else:
            val_mm = ((0.6*v) - 10)
            val = (((0.6*v) - 10)/1000) * check_area(area_m2,k)
            rain_dict_mm[k] = max(val_mm, 0)
            rain_dict_m3[k] = max(val, 0)
    return rain_dict_mm, rain_dict_m3

def check_crop_dataset(season_df, kc_df):
    kc_crops = kc_df['Crop'].values
    missing_crops = [
        row['Crop']
        for _, row in season_df.iterrows()
        if row['Crop'] not in kc_crops
    ]
    if missing_crops: print(f'Missing crops between datasets: {missing_crops}')

def monthly_kc(season_df, season_start, kc_df):
    out ={}
    for _, row in season_df.iterrows():
        monthdict = {f"{item:02d}": [] for item in range(1, 13)}
        start_date = datetime.strptime(season_start, "%Y-%m-%d")
        for stage in ('ini', 'dev', 'mid', 'late'):
            try:
                duration = kc_df.loc[kc_df['Crop']==row['Crop']][f'Duration ({stage})'].values[0]
                end_date = start_date+td(days=int(duration))
            except (KeyError, ValueError, IndexError):
                continue
            date_range = pd.date_range(start_date, end_date)
            for idate in date_range:
                monthdict[idate.strftime("%m")].append(kc_df.loc[kc_df['Crop']==row['Crop']][f'Kc ({stage})'].values[0])
            start_date = end_date + td(days=1)
        out[row['Crop']] = {key: round(sum(value) / len(value), 2) for key, value in monthdict.items() if value}
    return out

def crop_ETc(season_kc, season_df, ref_ET_dict, no_days_dict, crop_area):
    out ={}
    for crop, monthly_kc in season_kc.items():
        if crop in neglected_crops:
            continue
        ETc_dict = {}
        for month, kc in monthly_kc.items():
            perc = season_df.loc[season_df['Crop']==crop]['Percentage_Area'].values[0]
            ETc_month = kc * (ref_ET_dict[month]/1000) * no_days_dict[month] * (perc * crop_area)
            ETc_dict[month] = ETc_month
        out[crop] = ETc_dict
    return out

def monthly_ETc(crop_ETc_dict):
    out = {}
    for _, ETc_dict in crop_ETc_dict.items():
        for month, ETc in ETc_dict.items():
            if month in out:
                out[month] += ETc
            else:
                out[month] = ETc
    return out

def monthly_IWR(monthly_ETc, eff_rain_m3):
    return {
        month: monthly_ETc[month] - eff_rain_m3[month] for month in monthly_ETc
    }

def crop_water(year, ref_ET, eff_rain_m3, kc_df, kharif_df, rabi_df, zaid_df, crop_area):
    check_crop_dataset(kharif_df, kc_df)
    check_crop_dataset(rabi_df, kc_df)
    check_crop_dataset(zaid_df, kc_df)
    kharif_monthly_kc_dict = monthly_kc(kharif_df, season_dict(year)['kharif_start'], kc_df)
    rabi_monthly_kc_dict = monthly_kc(rabi_df, season_dict(year)['rabi_start'], kc_df)
    zaid_monthly_kc_dict = monthly_kc(zaid_df, season_dict(year)['zaid_start'], kc_df)
    # print(f'kharif monthly kc: {kharif_monthly_kc_dict}')
    # print(f'rabi monthly kc: {rabi_monthly_kc_dict}')
    # print(f'zaid monthly kc: {zaid_monthly_kc_dict}')
    no_days_dict = no_of_days(year)
    kharif_ETc_dict = crop_ETc(kharif_monthly_kc_dict, kharif_df, ref_ET, no_days_dict, check_area(crop_area,KHARIF_START_MONTH))
    rabi_ETc_dict = crop_ETc(rabi_monthly_kc_dict, rabi_df, ref_ET, no_days_dict, check_area(crop_area,RABI_START_MONTH))
    zaid_ETc_dict = crop_ETc(zaid_monthly_kc_dict, zaid_df, ref_ET, no_days_dict, check_area(crop_area,ZAID_START_MONTH))
    # print(f'kharif monthly crop ETc (m3): {kharif_ETc_dict}')
    # print(f'rabi monthly crop ETc (m3): {rabi_ETc_dict}')
    # print(f'zaid monthly crop ETc (m3): {zaid_ETc_dict}')
    kharif_month_ETc_dict = monthly_ETc(kharif_ETc_dict)
    rabi_month_ETc_dict = monthly_ETc(rabi_ETc_dict)
    zaid_month_ETc_dict = monthly_ETc(zaid_ETc_dict)
    # print(f'kharif monthly ETc (m3): {kharif_month_ETc_dict}')
    # print(f'rabi monthly ETc (m3): {rabi_month_ETc_dict}')
    # print(f'zaid monthly ETc (m3): {zaid_month_ETc_dict}')
    kharif_month_ETc_dict_mm = {k:(v/check_area(crop_area,k))*1000 for k,v in kharif_month_ETc_dict.items()}
    rabi_month_ETc_dict_mm = {k:(v/check_area(crop_area,k))*1000 for k,v in rabi_month_ETc_dict.items()}
    zaid_month_ETc_dict_mm = {k:(v/check_area(crop_area,k))*1000 for k,v in zaid_month_ETc_dict.items()}
    # print(f'kharif monthly ETc (mm): {kharif_month_ETc_dict_mm}')
    # print(f'rabi monthly ETc (mm): {rabi_month_ETc_dict_mm}')
    # print(f'zaid monthly ETc (mm): {zaid_month_ETc_dict_mm}')
    kharif_IWR_dict = monthly_IWR(kharif_month_ETc_dict, eff_rain_m3)
    rabi_IWR_dict = monthly_IWR(rabi_month_ETc_dict, eff_rain_m3)
    zaid_IWR_dict = monthly_IWR(zaid_month_ETc_dict, eff_rain_m3)
    # print(f'kharif monthly IWR (m3): {kharif_IWR_dict}')
    # print(f'rabi monthly IWR (m3): {rabi_IWR_dict}')
    # print(f'zaid monthly IWR (m3): {zaid_IWR_dict}')
    kharif_IWR_dict_corrected = {k: max(v, 0) for k,v in kharif_IWR_dict.items()}
    rabi_IWR_dict_corrected = {k: max(v, 0) for k,v in rabi_IWR_dict.items()}
    zaid_IWR_dict_corrected = {k: max(v, 0) for k,v in zaid_IWR_dict.items()}
    dataframe_generation(
        kharif_ETc_mm=kharif_month_ETc_dict_mm,
        kharif_ETc_m3=kharif_month_ETc_dict,
        rabi_ETc_mm=rabi_month_ETc_dict_mm,
        rabi_ETc_m3=rabi_month_ETc_dict)
    dataframe_generation(
        kharif_IWR_m3=kharif_IWR_dict,
        rabi_IWR_m3=rabi_IWR_dict)
    dataframe_generation(
        kharif_IWR_m3=kharif_IWR_dict_corrected,
        rabi_IWR_m3=rabi_IWR_dict_corrected)
    kharif_IWR = sum(kharif_IWR_dict_corrected.values())
    rabi_IWR = sum(rabi_IWR_dict_corrected.values())
    zaid_IWR = sum(zaid_IWR_dict_corrected.values())
    print(f'kharif IWR (m3): {kharif_IWR}')
    print(f'rabi IWR (m3): {rabi_IWR}')
    # print(f'zaid IWR (m3): {zaid_IWR}')
    return kharif_IWR + rabi_IWR

def availability_indicator_2(roi, year, rain_mm_dict):
    modis_ET = get_ET(season_dict(year)['kharif_start'], season_dict(year)['zaid_end'], roi)
    rain_mm = sum(rain_mm_dict.values())
    print(f'rainfall (mm): {rain_mm}')
    return modis_ET/rain_mm

def recharge(roi_area_m2, rain_mm_dict):
    rain_mm = sum(rain_mm_dict.values())
    cgwb_coeff = 0.07
    print(f'considering CGWB coefficient as (Wheathered Basalt) {round(cgwb_coeff*100,2)}%')
    recharge_mm = cgwb_coeff * rain_mm
    recharge_m3 = roi_area_m2*(recharge_mm/1000)
    return recharge_mm, recharge_m3

def main(year):
    # Boundary will be automatically fetched from the QGIS active layer
    active_lyr = iface.activeLayer()
    roi = lyr2ee(active_lyr)
    district = 'USM>N>B>D'
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
    # crop_m2 = crop_dict[year]
    crop_m2 = {
        'kharif': get_crop_m2(roi, season_dict(year)['kharif_start'], season_dict(year)['rabi_start']),
        'rabi': get_crop_m2(roi, season_dict(year)['rabi_start'], season_dict(year)['zaid_start']),
        'zaid': get_crop_m2(roi, season_dict(year)['zaid_start'], season_dict(year)['zaid_end'])
    }
    if isinstance(crop_m2, float):
        print(f'area of cropland in {year} is {round(crop_m2,2)} m2')
    else:
        print(f'crop area {year}: {[(k,round(v,2)) for k,v in crop_m2.items()]}')
    rain_mm_dict = get_rainfall(roi, year)
    ref_ET = get_refET(roi, year)
    eff_rain_mm, eff_rain_m3 = get_eff_rainfall_m3(crop_m2, rain_mm_dict)
    dataframe_generation(rainfall_mm=rain_mm_dict,eff_rainfall_mm=eff_rain_mm,eff_rainfall_m3=eff_rain_m3,ref_ET0_mm_per_day=ref_ET)
    crop_df = read_url(DIST_URL)
    kc_df = read_url(COEFF_URL)
    kharif_df = filter_df(crop_df, district, 'Kharif')
    rabi_df = filter_df(crop_df, district, 'Rabi')
    zaid_df = filter_df(crop_df, district, 'Zaid')
    # the dataset is sorted to consider only the CROPS_CONSIDERED number of crops
    print(f'considering only the {CROPS_CONSIDERED} number of crops for a season.')
    kharif_df = kharif_df.sort_values(by=['Percentage_Area'], ascending=False).head(CROPS_CONSIDERED).reset_index(drop=True)
    rabi_df = rabi_df.sort_values(by=['Percentage_Area'], ascending=False).head(CROPS_CONSIDERED).reset_index(drop=True)
    zaid_df = zaid_df.sort_values(by=['Percentage_Area'], ascending=False).head(CROPS_CONSIDERED).reset_index(drop=True)
    # method 1
    iwr_m3 = crop_water(year, ref_ET, eff_rain_m3, kc_df, kharif_df, rabi_df, zaid_df, crop_m2)
    blue_water_m3 = iwr_m3 + domestic_m3
    print(f'iwr(m3) {round(iwr_m3,2)} + domestic(m3) {round(domestic_m3,2)} = blue water(m3) {round(blue_water_m3,2)}')
    recharge_mm, recharge_m3 = recharge(geo_m2, rain_mm_dict)
    print(f'recharge (m3): {round(recharge_m3,2)}')
    availability_1 = blue_water_m3/recharge_m3
    print(f'Availability Indicator (method 1): {round(availability_1,2)}')
    # method 2
    availability_2 = availability_indicator_2(roi, year, rain_mm_dict)
    print(f'Availability Indicator (method 2): {round(availability_2,2)}')

main(YEAR)
