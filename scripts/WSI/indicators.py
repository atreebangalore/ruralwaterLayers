from calendar import monthrange
from collections import defaultdict
import ee

ee.Initialize()

DW_CROP_LABEL = 4
KHARIF_START_MONTH = 6
KHARIF_END_MONTH = 10
RABI_START_MONTH = 11
RABI_END_MONTH = 3
ZAID_START_MONTH = 4
ZAID_END_MONTH = 5

dwCol = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")

def season_dict(year):
    return {
        'kharif_start' : f'{year}-{KHARIF_START_MONTH:02d}-01',
        'kharif_end' : f'{year}-{KHARIF_END_MONTH:02d}-{monthrange(year, KHARIF_END_MONTH)[1]}',
        'rabi_start' : f'{year}-{RABI_START_MONTH:02d}-01',
        'rabi_end' : f'{year+1}-{RABI_END_MONTH:02d}-{monthrange(year+1, RABI_END_MONTH)[1]}',
        'zaid_start' : f'{year+1}-{ZAID_START_MONTH:02d}-01',
        'zaid_end' : f'{year+1}-{ZAID_END_MONTH:02d}-{monthrange(year+1, ZAID_END_MONTH)[1]}',
    }

def get_crop_mask(roi, crop_start, crop_end):
    dw = dwCol.filterDate(crop_start, crop_end).filterBounds(roi.geometry()).select(['label']).mode()
    return dw.eq(DW_CROP_LABEL).selfMask()

def area_image(image):
    return image.multiply(ee.Image.pixelArea())

def get_stats(image, roi):
    stat = image.reduceRegions(
        collection=roi,
        reducer=ee.Reducer.sum(),
        scale=10,
        crs='EPSG:4326',
    )
    return stat.getInfo()

def aggregate_dict(stat, unique_field):
    return {feat['properties'][unique_field]: feat['properties']['sum'] for feat in stat['features']}

def access_indicator(year, fc, unique_field):
    irrig_image = area_image(
        get_crop_mask(
            fc, season_dict(year)['rabi_start'], season_dict(year)['rabi_end']
        )
    )
    crop_image = area_image(
        get_crop_mask(
            fc, season_dict(year)['kharif_start'], season_dict(year)['rabi_end']
        )
    )
    
    irrig_stat = aggregate_dict(get_stats(irrig_image, fc), unique_field)
    crop_stat = aggregate_dict(get_stats(crop_image, fc), unique_field)
    access_scores = {village: -999.0 if crop_stat[village]==0 else irrig_stat[village]/crop_stat[village] for village in irrig_stat.keys()}
    return access_scores, crop_stat, irrig_stat

if __name__=='__main__':
    print('started!!!')
    fc = ee.FeatureCollection('users/balakumaranrm/PRADAN/villages_CH_WB')
    access_scores, kharif_area, rabi_area = access_indicator(2020, fc, 'village_na')
    print('completed!!!')