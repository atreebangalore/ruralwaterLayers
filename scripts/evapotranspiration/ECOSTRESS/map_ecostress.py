import ee
from ee_plugin import Map

# Initialize Earth Engine
ee.Initialize()

# Define the Feature and Year
district = ee.FeatureCollection('users/jaltolwelllabs/FeatureCol/Raichur').first()
yr = '2019'


collection = ee.ImageCollection('users/jaltolwelllabs/ET/ecostress')
yr2 = str(int(yr) + 1)

# GENERATE LIST OF (YEAR,MONTH) TUPLES
monthseq = ['06','07','08','09','10','11','12','01','02','03','04','05']
yearseq = [yr]*7 + [yr2]*5 
monthyearseq = [*zip(yearseq,monthseq)]
dates = [f'{year}-{month}-01' for year, month in monthyearseq]

# Function to calculate the mean composite for each month
def calculate_mean_composite(date):
    # Convert the month number to an EE date object
    # month_date = ee.Date.fromYMD(date[0], date[1], 1)
    month_date = ee.Date(date)

    # Filter the collection by month
    filtered = collection.filterDate(month_date, month_date.advance(1, 'month')).filterBounds(district.geometry())

    # Calculate the mean composite
    composite = ee.Algorithms.If(filtered.size()!=0, filtered.mean(), ee.Image.constant(0))

    # Multiply the composite by the number of days in the month
    days_in_month = month_date.advance(1, 'month').difference(month_date, 'day')
    composite = ee.Image(composite).multiply(days_in_month)

    # Set a property for the composite with the month name
    composite = composite.set('month', month_date.format('MMMYYYY'))

    return composite

# Map over the list of months to calculate the mean composites
composites = ee.ImageCollection.fromImages(ee.List(dates).map(calculate_mean_composite))

def getStats(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=district.geometry(),
        scale=70
    )
    return image.setMulti(stats)

# Apply the getStats function to the image collection
collection_with_stats = composites.map(getStats)

et_val_list = collection_with_stats.aggregate_array('b1').getInfo()
et_month_list = collection_with_stats.aggregate_array('month').getInfo()
monthly_et = dict(zip(et_month_list,et_val_list))

print(monthly_et)

hyd_image = composites.sum()

max_val = round(hyd_image.reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=district.geometry(),
        scale=70
    ).getInfo()['b1'],2)

min_val = round(hyd_image.reduceRegion(
        reducer=ee.Reducer.min(),
        geometry=district.geometry(),
        scale=70
    ).getInfo()['b1'],2)

print(f'visualize -> min: {min_val}, max: {max_val}')

clipped = hyd_image.clip(district)

viz = ['#d7191c', '#fdae61', '#ffffbf', '#abdda4', '#2b83ba']
Map.addLayer(clipped, {'palette': viz, 'min': min_val, 'max': max_val}, 'Ecostress')
Map.centerObject(clipped)
