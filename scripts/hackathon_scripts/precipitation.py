import ee
ee.Initialize()
from datetime import datetime
import pandas as pd
from pathlib import Path
from itertools import product

district_name = 'raichur'
village_list = ['sanbal', 'rampur']
start_year = 2000
end_year = 2021

precipitation_collection = ee.ImageCollection("users/jaltolwelllabs/IMD/rain")

print('started!!!')

def save_CSV(df, parameter, timestep, village_name, dataFol):
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

def get_rainfall(agg_col, pattern, unit, reducer, village_geometry):
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
def main(village_name):
    district_fc = ee.FeatureCollection(
        'users/jaltolwelllabs/hackathonDists/hackathon_dists'
        ).filter(ee.Filter.eq('district_n', district_name))
    village_fc = district_fc.filter(ee.Filter.eq('village_na', village_name))
    village_geometry = village_fc.geometry()

    dataFol = Path.home().joinpath("Data", "hackathon", district_name, village_name)
    dataFol.mkdir(parents=True, exist_ok=True)

    hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'sum')))
    yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm', 'sum', village_geometry)
    filepath = save_CSV(yr_df, 'TotalRain', 'hydYear', village_name, dataFol)
    print(f'completed: {filepath}')

    hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'mean')))
    yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm/day', 'mean', village_geometry)
    filepath = save_CSV(yr_df, 'MeanRain', 'hydYear', village_name, dataFol)
    print(f'completed: {filepath}')

    hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'median')))
    yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm/day', 'median', village_geometry)
    filepath = save_CSV(yr_df, 'MedianRain', 'hydYear', village_name, dataFol)
    print(f'completed: {filepath}')

    hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'max')))
    yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm/day', 'max', village_geometry)
    filepath = save_CSV(yr_df, 'MaxRain', 'hydYear', village_name, dataFol)
    print(f'completed: {filepath}')

    # hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'min')))
    # yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm/day', 'min', village_geometry)
    # filepath = save_CSV(yr_df, 'MinRain', 'hydYear', village_name, dataFol)
    # print(f'completed: {filepath}')

    hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'sum')))
    mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm', 'sum', village_geometry)
    filepath = save_CSV(mn_df, 'TotalRain', 'monthly', village_name, dataFol)
    print(f'completed: {filepath}')

    hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'mean')))
    mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm/day', 'mean', village_geometry)
    filepath = save_CSV(mn_df, 'MeanRain', 'monthly', village_name, dataFol)
    print(f'completed: {filepath}')

    hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'median')))
    mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm/day', 'median', village_geometry)
    filepath = save_CSV(mn_df, 'MedianRain', 'monthly', village_name, dataFol)
    print(f'completed: {filepath}')

    hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'max')))
    mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm/day', 'max', village_geometry)
    filepath = save_CSV(mn_df, 'MaxRain', 'monthly', village_name, dataFol)
    print(f'completed: {filepath}')

    # hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'min')))
    # mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm/day', 'min', village_geometry)
    # filepath = save_CSV(mn_df, 'MinRain', 'monthly', village_name, dataFol)
    # print(f'completed: {filepath}')

    da_df = get_rainfall(precipitation_collection, '%Y-%m-%d', 'mm', 'mean', village_geometry)
    filepath = save_CSV(da_df, 'Rain', 'daily', village_name, dataFol)
    print(f'completed: {filepath}')

for village in village_list:
    main(village)
