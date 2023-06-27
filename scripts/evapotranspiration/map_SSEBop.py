"""Generate SSEBop visualisation layer in QGIS for the given
GEE Feature in given year.
Copy paste or open the file in QGIS editor and correct the year and
change the variable "district" to required GEE Feature.
execute the script to create a ECOSTRESS layer.
"""
import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS

# Initialize Earth Engine
ee.Initialize()

# Define the Feature Collection, filter and dates
datameet = ee.FeatureCollection("users/jaltolwelllabs/FeatureCol/MH_KAR_TN_Jaltol")
district = datameet.filter(
    ee.Filter.And(
        ee.Filter.eq("State_N", "KARNATAKA"),
        ee.Filter.eq("Dist_N", "Shimoga"),
        ee.Filter.eq("SubDist_N", "Bhadravati"),
        ee.Filter.eq("Block_N", "Bhadravati"),
        ee.Filter.eq("VCT_N", "Hunasekatte"),
    )
)
start_date = "2019-06-01"
end_date = "2020-06-01"

# print the number of features in the filtered result, needs to be 1.
print(district.size().getInfo())
district = district.first()
# print the village name selected.
print(district.get("VCT_N").getInfo())

collection = ee.ImageCollection("users/jaltolwelllabs/ET/etSSEBop")
filtered = collection.filterDate(start_date, end_date).filterBounds(district.geometry())
# summation of all the monthly images in the date range.
sum_image = filtered.sum()
# clip the annual image to the Feature boundary.
clipped = sum_image.clip(district)

# calculate the maximum and minimum pixel values in the image
max_val = sum_image.reduceRegion(
    reducer=ee.Reducer.max(), geometry=district.geometry(), scale=1000
).getInfo()
min_val = sum_image.reduceRegion(
    reducer=ee.Reducer.min(), geometry=district.geometry(), scale=1000
).getInfo()
print(f"Max: {max_val}, min: {min_val}")

# add as a layer to QGIS
viz = ["#d7191c", "#fdae61", "#ffffbf", "#abdda4", "#2b83ba"]
Map.addLayer(
    clipped, {"palette": viz, "min": min_val["b1"], "max": max_val["b1"]}, "SSEBop"
)
Map.centerObject(clipped)
