import ee
from ee_plugin import Map

# Initialize Earth Engine
ee.Initialize()

# Define the ImageCollection and date range
collection = ee.ImageCollection('users/jaltolwelllabs/ET/ecostress')
datameet = ee.FeatureCollection('users/jaltolwelllabs/FeatureCol/District_Map_2011')

district = datameet.filter(
    ee.Filter.Or(
        ee.Filter.eq('ST_NM', 'Karnataka'),
        ee.Filter.eq('DISTRICT', 'Raichur')
        )).first()

district = ee.FeatureCollection('users/jaltolwelllabs/FeatureCol/Raichur').first()

filtered = collection.filterDate('2019-06-01', '2020-06-01').filterBounds(district.geometry())

sum_image = filtered.sum()
clipped = sum_image.clip(district)

max_val = sum_image.reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=district.geometry(),
        scale=70
    ).getInfo()

min_val = sum_image.reduceRegion(
        reducer=ee.Reducer.min(),
        geometry=district.geometry(),
        scale=70
    ).getInfo()

print(f'Max: {max_val}, min: {min_val}')
Map.addLayer(clipped, {'palette': ['pink','red'], 'min': min_val['b1'], 'max': max_val['b1']}, 'Ecostress')
Map.centerObject(clipped)
