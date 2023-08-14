"""Generate DynamicWorld visualisation layer in QGIS for the given
GEE Feature in given year.
Copy paste or open the file in QGIS editor and correct the year and
change the variable "district" to required GEE Feature.
execute the script to create a DynamicWorld layer.
"""
import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface
import json

# Initialize Earth Engine
ee.Initialize()

# Define the FeatureCollection, date range and filter the village
start_date = "2022-06-01"
end_date = "2023-06-01"
# datameet = ee.FeatureCollection("users/jaltolwelllabs/FeatureCol/MH_KAR_TN_Jaltol")
# district = datameet.filter(
#     ee.Filter.And(
#         ee.Filter.eq("State_N", "KARNATAKA"),
#         ee.Filter.eq("Dist_N", "Shimoga"),
#         ee.Filter.eq("SubDist_N", "Bhadravati"),
#         ee.Filter.eq("Block_N", "Bhadravati"),
#         ee.Filter.eq("VCT_N", "Hunasekatte"),
#     )
# )
# print(district.size().getInfo())
# district = district.first()
# print(district.get("VCT_N").getInfo())

# Boundary will be automatically fetched from the QGIS active layer
active_lyr = iface.activeLayer()
lyr_name = active_lyr.name()
lyr = QgsJsonExporter(active_lyr)
gs = lyr.exportFeatures(active_lyr.getFeatures())
gj = json.loads(gs)
for feature in gj["features"]:
    feature["id"] = f'{feature["id"]:04d}'
district = ee.FeatureCollection(gj)

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
# Map.centerObject(clipped)
