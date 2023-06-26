import ee
from ee_plugin import Map

# Initialize Earth Engine
ee.Initialize()

# Define the ImageCollection and date range
collection = ee.ImageCollection('users/jaltolwelllabs/ET/etSSEBop')
datameet = ee.FeatureCollection('users/jaltolwelllabs/FeatureCol/MH_KAR_TN_Jaltol')

district = datameet.filter(
    ee.Filter.And(
        ee.Filter.eq('State_N', 'KARNATAKA'),
        ee.Filter.eq('Dist_N', 'Shimoga'),
        ee.Filter.eq('SubDist_N', 'Bhadravati'),
        ee.Filter.eq('Block_N', 'Bhadravati'),
        ee.Filter.eq('VCT_N', 'Hunasekatte')
    ))
print(district.size().getInfo())
district = district.first()
print(district.get('VCT_N').getInfo())

filtered = collection.filterDate('2019-06-01', '2020-06-01').filterBounds(district.geometry())
sum_image = filtered.sum()
clipped = sum_image.clip(district)

max_val = sum_image.reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=district.geometry(),
        scale=1000
    ).getInfo()

min_val = sum_image.reduceRegion(
        reducer=ee.Reducer.min(),
        geometry=district.geometry(),
        scale=1000
    ).getInfo()

print(f'Max: {max_val}, min: {min_val}')
viz = ['#d7191c', '#fdae61', '#ffffbf', '#abdda4', '#2b83ba']
Map.addLayer(clipped, {'palette': viz, 'min': min_val['b1'], 'max': max_val['b1']}, 'SSEBop')
Map.centerObject(clipped)

