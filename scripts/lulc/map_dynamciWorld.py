"""Generate DynamicWorld visualisation layer in QGIS for the given
GEE Feature in given year.
Copy paste or open the file in QGIS editor and correct the year and
change the variable "district" to required GEE Feature.
execute the script to create a ECOSTRESS layer.
"""
import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS

# Initialize Earth Engine
ee.Initialize()

# Define the FeatureCollection, date range and filter the village
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
print(district.get("VCT_N").getInfo())

collection = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
# filter the collection and select the 'label' band
filtered = (
    collection.filterDate(start_date, end_date)
    .filterBounds(district.geometry())
    .select("label")
)
# compute the mode of LULC labels for the year resulting in an image
mode_image = filtered.mode()
# clip the image to boundary
clipped = mode_image.clip(district)

# add as layer to QGIS
viz = [
    "419bdf",
    "397d49",
    "88b053",
    "7a87c6",
    "e49635",
    "dfc35a",
    "c4281b",
    "a59b8f",
    "b39fe1",
]
Map.addLayer(clipped, {"palette": viz, "min": 0, "max": 8}, "DynamicWorld")
Map.centerObject(clipped)
