import ee
ee.Initialize()
import pandas as pd
from pathlib import Path
from calendar import monthrange
from itertools import product
from datetime import datetime

district_name = 'raichur'
village_name = 'sanbal'
start_year = 2015
end_year = 2022
DW_LABEL = 'tree' # 'crop' or 'tree'

DW = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")

district_fc = ee.FeatureCollection(
    'users/jaltolwelllabs/hackathonDists/hackathon_dists'
    ).filter(ee.Filter.eq('district_n', district_name))
roi = district_fc.filter(ee.Filter.eq('village_na', village_name))
# roi = village_fc.geometry()

class_label = 4 if DW_LABEL == 'crop' else 1

dataFol = Path.home().joinpath("Data", "hackathon", village_name)
dataFol.mkdir(parents=True, exist_ok=True)

print('started!!!')

def yearly_mode(year: int, label) -> ee.Image:
    fil = DW.filterDate(
        ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(ee.Number(year).add(1), 6, 1)
        ).filterBounds(roi).select(['label'])
    date = fil.first().get('system:time_start')
    return fil.mode().eq(label).set('system:time_start', date)

def monthly_mode(yr_mn, label):
    yr_mn = ee.List(yr_mn)
    st_date = ee.Date.fromYMD(yr_mn.getNumber(0), yr_mn.getNumber(1), 1)
    fil = DW.filterDate(
        st_date, st_date.advance(1, 'month')
        ).filterBounds(roi).select(['label'])
    date = ee.Algorithms.If(fil.size().eq(0), st_date.millis(), fil.first().get('system:time_start'))
    return ee.Algorithms.If(fil.size().eq(0), ee.Image.constant(0).rename('label').set('system:time_start', date), fil.mode().eq(label).set('system:time_start', date))

def getStats(image: ee.Image, geometry: ee.Geometry) -> ee.Image:
    area_image = image.multiply(ee.Image.pixelArea())
    stats = area_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10
    )
    return image.setMulti(stats)

def get_area(agg_col, pattern, unit, label_name):
    year_with_stats = agg_col.map(lambda image: getStats(image, roi))
    yr_values = year_with_stats.aggregate_array('label').getInfo()
    yr_dates = year_with_stats.aggregate_array('system:time_start').getInfo()
    yr_dates = [datetime.fromtimestamp(date / 1000).strftime(pattern) for date in yr_dates]

    yr_data = list(zip(yr_dates, yr_values))

    yr_dict = {year: {f'{label_name}({unit})': value} for year, value in yr_data}
    return pd.DataFrame(yr_dict).T

year_list = list(range(start_year, end_year+1))
month_numbers = list(range(1,13))
month_list = list(product(year_list,month_numbers))

hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_mode(year, class_label)))
yr_df = get_area(hyd_yr_col, '%Y', 'm2', DW_LABEL)
filename = f'{village_name}-DW-{DW_LABEL}-HydYear.csv'
path = dataFol.joinpath(filename)
yr_df.to_csv(path)
print(f'completed: {path}')

mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_mode(yr_mn, class_label)))
mn_df = get_area(mn_col, '%Y-%m', 'm2', DW_LABEL)
filename = f'{village_name}-DW-{DW_LABEL}-Monthly.csv'
path = dataFol.joinpath(filename)
mn_df.to_csv(path)
print(f'completed: {path}')
