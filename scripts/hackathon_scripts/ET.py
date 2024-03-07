import ee
ee.Initialize()
from datetime import datetime
import pandas as pd
from pathlib import Path
from itertools import product

district_name = 'raichur'
village_list = ['sanbal', 'rampur']
data_to_use = 'MODIS' # 'MODIS' or 'SSEBop'

print('started!!!')

def yearly_sum(year: int, reducer, data, band_name) -> ee.Image:
    if data == 'MODIS':
        collection = ee.Algorithms.If(ee.Number(year).gte(2021),
                        ee.ImageCollection("MODIS/061/MOD16A2").select(['ET']),
                        ee.ImageCollection("MODIS/006/MOD16A2").select(['ET']))
        # if year >= 2021:
        #     collection = ee.ImageCollection("MODIS/061/MOD16A2").select(['ET'])
        # else:
        #     collection = ee.ImageCollection("MODIS/006/MOD16A2").select(['ET'])
    else:
        collection = ee.ImageCollection('users/jaltolwelllabs/ET/etSSEBop')
    fil = ee.ImageCollection(collection).filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(ee.Number(year).add(1), 6, 1))
    # date = fil.first().get('system:time_start')
    date = ee.Algorithms.If(fil.size().eq(0), ee.Date.fromYMD(year, 6, 1).millis(), fil.first().get('system:time_start'))
    fil = ee.ImageCollection(ee.Algorithms.If(fil.size().eq(0), ee.List(ee.Image.constant(0).rename(band_name).set('system:time_start', date)), fil))
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

def monthly_sum(yr_mn, reducer, data, band_name):
    yr_mn = ee.List(yr_mn)
    year = yr_mn.getNumber(0)
    if data == 'MODIS':
        collection = ee.Algorithms.If(ee.Number(year).gte(2021),
                        ee.ImageCollection("MODIS/061/MOD16A2").select(['ET']),
                        ee.ImageCollection("MODIS/006/MOD16A2").select(['ET']))
        # if year >= 2021:
        #     collection = ee.ImageCollection("MODIS/061/MOD16A2").select(['ET'])
        # else:
        #     collection = ee.ImageCollection("MODIS/006/MOD16A2").select(['ET'])
    else:
        collection = ee.ImageCollection('users/jaltolwelllabs/ET/etSSEBop')
    st_date = ee.Date.fromYMD(yr_mn.getNumber(0), yr_mn.getNumber(1), 1)
    fil = ee.ImageCollection(collection).filterDate(st_date, st_date.advance(1, 'month'))
    # date = fil.first().get('system:time_start')
    date = ee.Algorithms.If(fil.size().eq(0), st_date.millis(), fil.first().get('system:time_start'))
    fil = ee.ImageCollection(ee.Algorithms.If(fil.size().eq(0), ee.ImageCollection([ee.Image.constant(0).rename(band_name).set('system:time_start', date)]), fil))
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
        scale=250
    )
    return image.setMulti(stats)

def get_rainfall(agg_col, pattern, unit, reducer, band_name, data, village_geometry):
    year_with_stats = agg_col.map(lambda image: getStats(image, village_geometry, reducer))

    yr_rain_values = year_with_stats.aggregate_array(band_name).getInfo()
    yr_dates = year_with_stats.aggregate_array('system:time_start').getInfo()
    yr_dates = [datetime.fromtimestamp(date / 1000).strftime(pattern) for date in yr_dates]

    yr_rainfall_data = list(zip(yr_dates, yr_rain_values))

    yr_dict = {year: {f'ET({unit})': value*0.1 if data=='MODIS' else value} for year, value in yr_rainfall_data}
    return pd.DataFrame(yr_dict).T

def save_CSV(df, parameter, timestep, village_name, data, dataFol):
    filename = f'{village_name}-{parameter}-{timestep}-{data}.csv'
    path = dataFol.joinpath(filename)
    df.to_csv(path)
    return path

def main(village_name):
    district_fc = ee.FeatureCollection(
        'users/jaltolwelllabs/hackathonDists/hackathon_dists'
        ).filter(ee.Filter.eq('district_n', district_name))
    village_fc = district_fc.filter(ee.Filter.eq('village_na', village_name))
    village_geometry = village_fc.geometry()

    dataFol = Path.home().joinpath("Data", "hackathon", district_name, village_name)
    dataFol.mkdir(parents=True, exist_ok=True)
    if data_to_use == 'MODIS':
        start_year = 2001
        end_year = 2022
        year_list = list(range(start_year, end_year+1))
        month_numbers = list(range(1,13))
        month_list = list(product(year_list,month_numbers))

        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'sum', 'MODIS', 'ET')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'kg/m2', 'sum', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(yr_df, 'TotalET', 'hydYear', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'mean', 'MODIS', 'ET')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'kg/m2/8day', 'mean', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(yr_df, 'MeanET', 'hydYear', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'median', 'MODIS', 'ET')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'kg/m2/8day', 'median', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(yr_df, 'MedianET', 'hydYear', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'max', 'MODIS', 'ET')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'kg/m2/8day', 'max', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(yr_df, 'MaxET', 'hydYear', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'min', 'MODIS', 'ET')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'kg/m2/8day', 'min', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(yr_df, 'MinET', 'hydYear', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'sum', 'MODIS', 'ET')))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'kg/m2', 'sum', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(mn_df, 'TotalET', 'monthly', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'mean', 'MODIS', 'ET')))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'kg/m2/8day', 'mean', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(mn_df, 'MeanET', 'monthly', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'median', 'MODIS', 'ET')))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'kg/m2/8day', 'median', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(mn_df, 'MedianET', 'monthly', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'max', 'MODIS', 'ET')))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'kg/m2/8day', 'max', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(mn_df, 'MaxET', 'monthly', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'min', 'MODIS', 'ET')))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'kg/m2/8day', 'min', 'ET', 'MODIS', village_geometry)
        filepath = save_CSV(mn_df, 'MinET', 'monthly', village_name, 'MODIS', dataFol)
        print(f'completed: {filepath}')

    if data_to_use == 'SSEBop':
        start_year = 2003
        end_year = 2020
        year_list = list(range(start_year, end_year+1))
        month_numbers = list(range(1,13))
        month_list = list(product(year_list,month_numbers))
        
        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'sum', 'SSEBop', 'b1')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm', 'sum', 'b1', 'SSEBop', village_geometry)
        filepath = save_CSV(yr_df, 'TotalET', 'hydYear', village_name, 'SSEBop', dataFol)
        print(f'completed: {filepath}')

        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'mean', 'SSEBop', 'b1')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm/month', 'mean', 'b1', 'SSEBop', village_geometry)
        filepath = save_CSV(yr_df, 'MeanET', 'hydYear', village_name, 'SSEBop', dataFol)
        print(f'completed: {filepath}')

        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'median', 'SSEBop', 'b1')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm/month', 'median', 'b1', 'SSEBop', village_geometry)
        filepath = save_CSV(yr_df, 'MedianET', 'hydYear', village_name, 'SSEBop', dataFol)
        print(f'completed: {filepath}')

        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'max', 'SSEBop', 'b1')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm/month', 'max', 'b1', 'SSEBop', village_geometry)
        filepath = save_CSV(yr_df, 'MaxET', 'hydYear', village_name, 'SSEBop', dataFol)
        print(f'completed: {filepath}')

        hyd_yr_col = ee.ImageCollection(ee.List(year_list).map(lambda year: yearly_sum(year, 'min', 'SSEBop', 'b1')))
        yr_df = get_rainfall(hyd_yr_col, '%Y', 'mm/month', 'min', 'b1', 'SSEBop', village_geometry)
        filepath = save_CSV(yr_df, 'MinET', 'hydYear', village_name, 'SSEBop', dataFol)
        print(f'completed: {filepath}')

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'sum', 'SSEBop', 'b1')))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm/month', 'sum', 'b1', 'SSEBop', village_geometry)
        filepath = save_CSV(mn_df, 'ET', 'monthly', village_name, 'SSEBop', dataFol)
        print(f'completed: {filepath}')

        # hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'mean', 'SSEBop', 'b1')))
        # mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm/month', 'mean', 'b1', 'SSEBop', village_geometry)
        # filepath = save_CSV(mn_df, 'MeanET', 'monthly', village_name, 'SSEBop', dataFol)
        # print(f'completed: {filepath}')

        # hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'median', 'SSEBop', 'b1')))
        # mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm/month', 'median', 'b1', 'SSEBop', village_geometry)
        # filepath = save_CSV(mn_df, 'MedianET', 'monthly', village_name, 'SSEBop', dataFol)
        # print(f'completed: {filepath}')

        # hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'max', 'SSEBop', 'b1')))
        # mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm/month', 'max', 'b1', 'SSEBop', village_geometry)
        # filepath = save_CSV(mn_df, 'MaxET', 'monthly', village_name, 'SSEBop', dataFol)
        # print(f'completed: {filepath}')

        # hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_sum(yr_mn, 'min', 'SSEBop', 'b1')))
        # mn_df = get_rainfall(hyd_mn_col, '%Y-%m', 'mm/month', 'min', 'b1', 'SSEBop', village_geometry)
        # filepath = save_CSV(mn_df, 'MinET', 'monthly', village_name, 'SSEBop', dataFol)
        # print(f'completed: {filepath}')

for village in village_list:
    main(village)
