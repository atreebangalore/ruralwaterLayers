import ee
from ee_plugin import Map

# Initialize Earth Engine
ee.Initialize()

# Define the ImageCollection and date range
collection = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
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

filtered = collection.filterDate('2019-06-01', '2020-06-01').filterBounds(district.geometry()).select('label')
mode_image = filtered.mode()
clipped = mode_image.clip(district)

viz = ['419bdf', '397d49', '88b053', '7a87c6', 'e49635', 'dfc35a', 'c4281b',
    'a59b8f', 'b39fe1']

Map.addLayer(clipped, {'palette': viz, 'min': 0, 'max': 8}, 'DynamicWorld')
Map.centerObject(clipped)
