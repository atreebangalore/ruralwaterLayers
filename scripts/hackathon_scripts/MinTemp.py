import ee
ee.Initialize()
from datetime import datetime
import pandas as pd
from pathlib import Path
from itertools import product

district_name = 'raichur'
village_name = 'sanbal'
start_year = 2000
end_year = 2020

district_fc = ee.FeatureCollection(
    'users/jaltolwelllabs/hackathonDists/hackathon_dists'
    ).filter(ee.Filter.eq('district_n', district_name))
village_fc = district_fc.filter(ee.Filter.eq('village_na', village_name))
village_geometry = village_fc.geometry()
precipitation_collection = ee.ImageCollection("users/jaltolwelllabs/IMD/minTemp")

dataFol = Path.home().joinpath("Data", "hackathon", village_name)
dataFol.mkdir(parents=True, exist_ok=True)

print('started!!!')

def save_CSV(df, parameter, timestep, village_name):
    filename = f'{village_name}-{parameter}-{timestep}.csv'
    path = dataFol.joinpath(filename)
    df.to_csv(path)
    return path

def yearly_sum(year: int, reducer) -> ee.Image:
    fil = precipitation_collection.filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(ee.Number(year).add(1), 6, 1))
    date = fil.first().get('system:time_start')
    if reducer == 'median':
        return fil.median().set('system:time_start', date)
    elif reducer =='mean':
        return fil.mean().set('system:time_start', date)
    elif reducer =='max':
        return fil.max().set('system:time_start', date)
    elif reducer =='min':
        return fil.min().set('system:time_start', date)
    else:
        return fil.sum().set('system:time_start', date)

def monthly_sum(yr_mn, reducer):
    yr_mn = ee.List(yr_mn)
    st_date = ee.Date.fromYMD(yr_mn.getNumber(0), yr_mn.getNumber(1), 1)
    fil = precipitation_collection.filterDate(st_date, st_date.advance(1, 'month'))
    date = fil.first().get('system:time_start')
    if reducer == 'median':
        return fil.median().set('system:time_start', date)
    elif reducer =='mean':
        return fil.mean().set('system:time_start', date)
    elif reducer =='max':
        return fil.max().set('system:time_start', date)
    elif reducer =='min':
        return fil.min().set('system:time_start', date)
    else:
        return fil.sum().set('system:time_start', date)

def getStats(image: ee.Image, geometry: ee.Geometry, reducer) -> ee.Image:
    if reducer == 'min':
        red = ee.Reducer.min()
    elif reducer == 'max':
        red = ee.Reducer.max()
    elif reducer == 'median':
        red = ee.Reducer.median()
    else:
        red = ee.Reducer.mean()
    stats = image.reduceRegion(
        reducer=red,
        geometry=geometry,
        scale=1000
    )
    return image.setMulti(stats)

def get_rainfall(agg_col, pattern, unit, reducer):
    year_with_stats = agg_col.map(lambda image: getStats(image, village_geometry, reducer))

    yr_rain_values = year_with_stats.aggregate_array('b1').getInfo()
    yr_dates = year_with_stats.aggregate_array('system:time_start').getInfo()
    yr_dates = [datetime.fromtimestamp(date / 1000).strftime(pattern) for date in yr_dates]

    yr_rainfall_data = list(zip(yr_dates, yr_rain_values))

    yr_dict = {year: {f'rain({unit})': value} for year, value in yr_rainfall_data}
    return pd.DataFrame(yr_dict).T


year_list = list(range(start_year, end_year+1))
month_numbers = list(range(1,13))
month_list = list(product(year_list,month_numbers))

# hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'sum')))
# yr_df = get_rainfall(hyd_yr_col, '%Y', 'degC', 'sum')
# filepath = save_CSV(yr_df, 'TotalMinTemp', 'hydYear', village_name)
# print(f'completed: {filepath}')

hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'mean')))
yr_df = get_rainfall(hyd_yr_col, '%Y', 'degC/day', 'mean')
filepath = save_CSV(yr_df, 'MeanMinTemp', 'hydYear', village_name)
print(f'completed: {filepath}')

hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'median')))
yr_df = get_rainfall(hyd_yr_col, '%Y', 'degC/day', 'median')
filepath = save_CSV(yr_df, 'MedianMinTemp', 'hydYear', village_name)
print(f'completed: {filepath}')

hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'max')))
yr_df = get_rainfall(hyd_yr_col, '%Y', 'degC/day', 'max')
filepath = save_CSV(yr_df, 'MaxMinTemp', 'hydYear', village_name)
print(f'completed: {filepath}')

# hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'min')))
# yr_df = get_rainfall(hyd_yr_col, '%Y', 'degC/day', 'min')
# filepath = save_CSV(yr_df, 'MinMinTemp', 'hydYear', village_name)
# print(f'completed: {filepath}')

# hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'sum')))
# mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'degC', 'sum')
# filepath = save_CSV(mn_df, 'TotalMinTemp', 'monthly', village_name)
# print(f'completed: {filepath}')

hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'mean')))
mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'degC/day', 'mean')
filepath = save_CSV(mn_df, 'MeanMinTemp', 'monthly', village_name)
print(f'completed: {filepath}')

hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'median')))
mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'degC/day', 'median')
filepath = save_CSV(mn_df, 'MedianMinTemp', 'monthly', village_name)
print(f'completed: {filepath}')

hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'max')))
mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'degC/day', 'max')
filepath = save_CSV(mn_df, 'MaxMinTemp', 'monthly', village_name)
print(f'completed: {filepath}')

# hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'min')))
# mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'degC/day', 'min')
# filepath = save_CSV(mn_df, 'MinMinTemp', 'monthly', village_name)
# print(f'completed: {filepath}')

da_df = get_rainfall(precipitation_collection, '%Y-%m-%d', 'degC', 'mean')
filepath = save_CSV(da_df, 'MinTemp', 'daily', village_name)
print(f'completed: {filepath}')
