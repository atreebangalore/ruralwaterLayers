import ee
ee.Initialize()
from qgis.core import (
    QgsJsonExporter,
)
from qgis.utils import iface
import json
import pandas as pd
from pathlib import Path

YEAR = 2019

active_lyr = iface.activeLayer()
lyr_name = active_lyr.name()
lyr = QgsJsonExporter(active_lyr)
gs = lyr.exportFeatures(active_lyr.getFeatures())
gj = json.loads(gs)
for feature in gj['features']:
    feature['id'] = f'{feature["id"]:04d}'
roi = ee.FeatureCollection(gj)
dataFol = Path.home().joinpath("Data","et","ecostress")
dataFol.mkdir(parents=True, exist_ok=True)
out_file = dataFol.joinpath(f'{lyr_name}-{YEAR}.csv')
print(f'layer to ee: {lyr_name}')

START_DATE = f'{YEAR}-06-01'
END_DATE = f'{YEAR+1}-06-01'
# Define the Sentinel-2 Surface Reflectance Image Collection
s2_collection = ee.ImageCollection('users/jaltolwelllabs/ET/ecostress')

# Filter the Image Collection by the region of interest and date range
filtered_collection = s2_collection.filterBounds(roi).filterDate(START_DATE, END_DATE)

total_area = roi.geometry().area()

# Function to calculate the percentage of area covered by the mosaic
def calculateMosaicCoverage(image):
    # Calculate the area covered by the image mosaic
    area_covered = image.select(0).multiply(ee.Image.pixelArea()).gt(0).reduceRegion(ee.Reducer.sum(), roi, 70)

    # Calculate the percentage of area covered by the mosaic
    percentage_coverage = ee.Number(area_covered.get(area_covered.keys().get(0))).divide(ee.Number(total_area)).multiply(100)

    return image.set('percentage_coverage', percentage_coverage)

# Map over the filtered Image Collection to calculate mosaic coverage for each image
collection_with_coverage = filtered_collection.map(calculateMosaicCoverage)

# Function to calculate the number of images per month and the average percentage coverage
def countImagesAndCoverage(month):
    # Filter images for the specified month
    images_for_month = collection_with_coverage.filter(ee.Filter.calendarRange(month, month, 'month'))

    # Get the count of images for the month
    count = images_for_month.size()

    # Calculate the average percentage coverage for the month
    coverage_sum = images_for_month.aggregate_sum('percentage_coverage')
    coverage_avg = coverage_sum.divide(count)

    return ee.Feature(None, {'Month': month, 'Number of Images': count, 'Percentage Coverage (%)': coverage_avg})

# Get the distinct months in the collection
months = ee.List.sequence(1, 12)

# Map over the list of months to get the count of images and coverage for each month
monthly_image_coverage = ee.FeatureCollection(months.map(countImagesAndCoverage))

# Convert the Earth Engine FeatureCollection to a Pandas DataFrame
fetched = {i['properties']['Month']: i['properties'] for i in monthly_image_coverage.getInfo()['features']}
df = pd.DataFrame(fetched).T
df['Month'] = df['Month'].astype(int).apply(lambda x: f'{YEAR}-{x:02d}' if x>5 else f'{YEAR+1}-{x:02d}')
df.sort_values(by=['Month'], inplace=True)

# Export the DataFrame to a CSV file
df.to_csv(out_file, index=False)
print(f'output: {out_file}')