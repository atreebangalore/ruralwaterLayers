import ee
ee.Initialize()
from ee_plugin import Map

latitude = 26.581561
longitude = 77.289162
buffer_dist = 1000 # m
ndwi_threshold = 0.1

S2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")

geom = ee.Geometry.Point([longitude, latitude])
buff = geom.buffer(buffer_dist)

date_ranges = [
    {'start': '2023-06-01', 'end': '2023-12-31'},
    {'start': '2022-06-01', 'end': '2022-12-31'},
    {'start': '2021-06-01', 'end': '2021-12-31'}
]

def calc_ndwi(image):
    return image.normalizedDifference(['B3', 'B8']).gte(ndwi_threshold).rename('NDWI')

def filter_by_date_range(date_range):
    start_date = ee.Date(date_range['start'])
    end_date = ee.Date(date_range['end'])
    return S2.filterDate(start_date, end_date).filterBounds(
        buff).filter(ee.Filter.lte('CLOUDY_PIXEL_PERCENTAGE', 30)).map(calc_ndwi).sum()



filtered_collections = list(map(filter_by_date_range, date_ranges))
filtered_collection = ee.ImageCollection.fromImages(filtered_collections)

ndwi = filtered_collection.sum().gte(1)#.map(calc_ndwi).sum().gte(1)

Map.addLayer(ndwi, {'min':0, 'max':1, 'palette':['white','blue']},'NDWI')
