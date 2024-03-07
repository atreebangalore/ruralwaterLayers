import ee
ee.Initialize()
from datetime import datetime
import pandas as pd
from pathlib import Path
from itertools import product

district_name = 'raichur'
village_list = ['sanbal', 'rampur']
# start_year = 2016
# end_year = 2022

sm_surface = ee.ImageCollection("NASA/SMAP/SPL4SMGP/007").select(['sm_surface'])
sm_rootzone = ee.ImageCollection("NASA/SMAP/SPL4SMGP/007").select(['sm_rootzone'])
lai = ee.ImageCollection("MODIS/061/MYD15A2H").select(['Lai_500m'])

print('started!!!')

def monthly_mean(yr_mn, reducer, collection):
    yr_mn = ee.List(yr_mn)
    st_date = ee.Date.fromYMD(yr_mn.getNumber(0), yr_mn.getNumber(1), 1)
    fil = collection.filterDate(st_date, st_date.advance(1, 'month'))
    date = fil.first().get('system:time_start')
    if reducer == 'median':
        return fil.median().set('system:time_start', date)
    elif reducer =='mean':
        return fil.mean().set('system:time_start', date)
    elif reducer =='max':
        return fil.max().set('system:time_start', date)
    else:
        return fil.min().set('system:time_start', date)

def getStats(image: ee.Image, geometry: ee.Geometry, reducer, multiplier) -> ee.Image:
    if reducer == 'min':
        red = ee.Reducer.min()
    elif reducer == 'max':
        red = ee.Reducer.max()
    elif reducer == 'median':
        red = ee.Reducer.median()
    else:
        red = ee.Reducer.mean()
    stats = image.multiply(multiplier).reduceRegion(
        reducer=red,
        geometry=geometry,
        scale=1000
    )
    return image.setMulti(stats)

def get_rainfall(agg_col, pattern, unit, reducer, heading, band_name, multiplier, village_geometry):
    year_with_stats = agg_col.map(lambda image: getStats(image, village_geometry, reducer, multiplier))

    yr_rain_values = year_with_stats.aggregate_array(band_name).getInfo()
    yr_dates = year_with_stats.aggregate_array('system:time_start').getInfo()
    yr_dates = [datetime.fromtimestamp(date / 1000).strftime(pattern) for date in yr_dates]

    yr_rainfall_data = list(zip(yr_dates, yr_rain_values))

    yr_dict = {year: {f'{heading}({unit})': value} for year, value in yr_rainfall_data}
    return pd.DataFrame(yr_dict).T

def save_CSV(df, dataFol, parameter, timestep, village_name):
    filename = f'{village_name}-{parameter}-{timestep}.csv'
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

    end_year = 2022
    for i in [(sm_surface, 'SoilMoistureSurface', 'sm_surface', 'VolumeFraction', 1), (sm_rootzone, 'SoilMoistureRootZone', 'sm_rootzone', 'VolumeFraction', 1), (lai, 'LeafAreaIndex', 'Lai_500m', 'AreaFraction', 0.1)]:
        data, heading, band_name, unit, multiplier = i
        start_year = 2003 if heading == 'LeafAreaIndex' else 2016
        year_list = list(range(start_year, end_year+1))
        month_numbers = list(range(1,13))
        month_list = list(product(year_list,month_numbers))

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_mean(yr_mn, 'mean', data)))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', unit, 'mean', heading, band_name, multiplier, village_geometry)
        filepath = save_CSV(mn_df, dataFol, f'Mean{heading}', 'monthly', village_name)
        print(f'completed: {filepath}')

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_mean(yr_mn, 'median', data)))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', unit, 'median', heading, band_name, multiplier, village_geometry)
        filepath = save_CSV(mn_df, dataFol, f'Median{heading}', 'monthly', village_name)
        print(f'completed: {filepath}')

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_mean(yr_mn, 'max', data)))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', unit, 'max', heading, band_name, multiplier, village_geometry)
        filepath = save_CSV(mn_df, dataFol, f'Max{heading}', 'monthly', village_name)
        print(f'completed: {filepath}')

        hyd_mn_col = ee.ImageCollection(ee.List(month_list).map(lambda yr_mn: monthly_mean(yr_mn, 'min', data)))
        mn_df = get_rainfall(hyd_mn_col, '%Y-%m', unit, 'min', heading, band_name, multiplier, village_geometry)
        filepath = save_CSV(mn_df, dataFol, f'Min{heading}', 'monthly', village_name)
        print(f'completed: {filepath}')

for village in village_list:
    main(village)
