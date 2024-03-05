import ee
ee.Initialize()
import pandas as pd
from pathlib import Path
from calendar import monthrange

district_name = 'raichur'
village_name = 'sanbal'
start_year = 2020
end_year = 2022
data_to_use = 'MODIS' # 'Landsat7', 'Landsat8', 'HLS' or 'MODIS'
mask_cropland = True
NDVI_THRESHOLD = 0.3
DW_CROP_LABEL = 4

L7 = ee.ImageCollection("LANDSAT/LE07/C02/T1_TOA")
L8 = ee.ImageCollection("LANDSAT/LC08/C02/T1_TOA")
MODIS = ee.ImageCollection("MODIS/061/MOD13Q1")
DW = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
HLS = ee.ImageCollection("NASA/HLS/HLSL30/v002")

district_fc = ee.FeatureCollection(
    'users/jaltolwelllabs/hackathonDists/hackathon_dists'
    ).filter(ee.Filter.eq('district_n', district_name))
roi = district_fc.filter(ee.Filter.eq('village_na', village_name))
# roi = village_fc.geometry()

dataFol = Path.home().joinpath("Data", "hackathon", village_name)
dataFol.mkdir(parents=True, exist_ok=True)

print('started!!!')

def feature_stats(image: ee.Image, fc: ee.FeatureCollection, threshold: float, scale_val: int):
    class_image = image.gte(threshold)
    area_image = class_image.multiply(ee.Image.pixelArea())
    area = area_image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.sum(),
        scale=scale_val,
        crs="EPSG:4326",
    )
    return area.getInfo()

def get_crop_mask(roi, crop_start, crop_end):
    dw = DW.filterDate(crop_start, crop_end).filterBounds(roi).select(['label']).mode()
    return dw.eq(DW_CROP_LABEL).selfMask()

out_dict = {}
for year in range(start_year,end_year+1):
    dict_key = f'ndvi_gte{NDVI_THRESHOLD}{"_DWcropMask" if mask_cropland else ""}_{data_to_use}_{year}'
    out_dict[dict_key] = {}
    crop_mask = get_crop_mask(roi, f'{max(year, 2015)}-10-01', f'{max(year, 2015)+1}-02-01')
    # for mn in range(9,15):
    #     if mn>12:
    #         month=mn-12
    #         year=yr+1
    #     else:
    #         month=mn
    #         year=yr
    for month in range(1,13):
        print(f'{data_to_use} processing: {year},{month}')
        out_dict[dict_key][f'{year}-{month:02d}'] = {}
        if data_to_use=='Landsat7':
            # im = L7.filterDate(f'{year}-06-01',f'{year+1}-06-01').filterBounds(roi).median()
            im = L7.filterDate(f'{year}-{month:02d}-01',f'{year}-{month:02d}-{monthrange(year, month)[1]}').filterBounds(roi)#.median()
            if im.size().getInfo()==0:
                continue
            ndvi = im.median().normalizedDifference(['B4', 'B3']).rename('NDVI')
            if mask_cropland:
                ndvi = ndvi.updateMask(crop_mask)
        elif data_to_use=='Landsat8':
            if year < 2013:
                continue
            im = L8.filterDate(f'{year}-{month:02d}-01',f'{year}-{month:02d}-{monthrange(year, month)[1]}').filterBounds(roi)#.median()
            if im.size().getInfo()==0:
                continue
            ndvi = im.median().normalizedDifference(['B5', 'B4']).rename('NDVI')
            if mask_cropland:
                ndvi = ndvi.updateMask(crop_mask)
        elif data_to_use=='HLS':
            if year < 2013:
                continue
            im = HLS.filterDate(f'{year}-{month:02d}-01',f'{year}-{month:02d}-{monthrange(year, month)[1]}').filterBounds(roi)#.median()
            if im.size().getInfo()==0:
                continue
            ndvi = im.median().normalizedDifference(['B5', 'B4']).rename('NDVI')
            if mask_cropland:
                ndvi = ndvi.updateMask(crop_mask)
        elif data_to_use=='MODIS':
            # ndvi = MODIS.filterDate(f'{year}-06-01',f'{year+1}-06-01').filterBounds(roi).select('NDVI').reduce(ee.Reducer.median()).multiply(0.0001)
            ndvi = MODIS.filterDate(f'{year}-{month:02d}-01',f'{year}-{month:02d}-{monthrange(year, month)[1]}').filterBounds(roi).select('NDVI').reduce(ee.Reducer.median()).multiply(0.0001)
            if mask_cropland:
                ndvi = ndvi.updateMask(crop_mask)
        else:
            raise ValueError('data not specified correctly!!!')
        stats = feature_stats(ndvi, roi, NDVI_THRESHOLD, 30)
        for feature in stats['features']:
            name = f"{feature['properties']['village_na']}NDVI(m2)"
            ndvi_value = feature['properties']['sum']
            out_dict[dict_key][f'{year}-{month:02d}'][name] = ndvi_value
# print(out_dict)

for year, df_dict in out_dict.items():
    df = pd.DataFrame(df_dict).T
    out_file = dataFol.joinpath(f"{year}.csv")
    df.to_csv(out_file)
    print(out_file)
