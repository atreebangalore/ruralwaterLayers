"""Generate MODIS AET & PET visualisation layer in QGIS for the given
GEE Feature in given year.
Copy paste or open the file in QGIS editor and correct the year and
while execution the active layer in QGIS workspace will be considered as the
boundary and images will be clipped to that extent.
"""
import json
from typing import Tuple

import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface

# Initialize Earth Engine
ee.Initialize()

# input - enter the year (hydrological)
YEAR = 2021

# Boundary will be automatically fetched from the QGIS active layer
active_lyr = iface.activeLayer()
lyr_name = active_lyr.name()
lyr = QgsJsonExporter(active_lyr)
gs = lyr.exportFeatures(active_lyr.getFeatures())
gj = json.loads(gs)
for feature in gj["features"]:
    feature["id"] = f'{feature["id"]:04d}'
roi = ee.FeatureCollection(gj)
print(f"layer to ee: {lyr_name}")

# based on the year entered select an ImageCollection
if YEAR >= 2021:
    col = ee.ImageCollection("MODIS/061/MOD16A2")
else:
    col = ee.ImageCollection("MODIS/006/MOD16A2")

total_filtered = col.filterDate(f"{YEAR}-06-01", f"{YEAR+1}-06-01").filterBounds(
    roi.geometry()
)
kharif_filtered = col.filterDate(f"{YEAR}-06-01", f"{YEAR}-10-01").filterBounds(
    roi.geometry()
)
rabi_filtered = col.filterDate(f"{YEAR}-10-01", f"{YEAR+1}-02-01").filterBounds(
    roi.geometry()
)
zaid_filtered = col.filterDate(f"{YEAR+1}-02-01", f"{YEAR+1}-06-01").filterBounds(
    roi.geometry()
)


def calculations(
    filtered_col: ee.ImageCollection, bound: ee.FeatureCollection, band: str
) -> Tuple[ee.Image, float, float]:
    image = filtered_col.select([band]).sum().multiply(0.1)  # multiply scale
    max_val = image.reduceRegion(
        reducer=ee.Reducer.max(), geometry=bound.geometry(), scale=100
    ).getInfo()[band]
    min_val = image.reduceRegion(
        reducer=ee.Reducer.min(), geometry=bound.geometry(), scale=100
    ).getInfo()[band]
    return image, max_val, min_val


viz = ["#d7191c", "#fdae61", "#ffffbf", "#abdda4", "#2b83ba"]


def map_images(
    filtered_col: ee.ImageCollection,
    bound: ee.FeatureCollection,
    band: str,
    timeframe: str,
) -> None:
    image, max_val, min_val = calculations(filtered_col, bound, band)
    print(f"{timeframe}{YEAR} -> max: {max_val}, min: {min_val}")
    Map.addLayer(
        image.clip(bound),
        {"palette": viz, "min": min_val, "max": max_val},
        f"{timeframe}-{band}-{YEAR}",
    )


for feat in zip(
    [total_filtered, kharif_filtered, rabi_filtered, zaid_filtered],
    ["total", "kharif", "rabi", "zaid"],
):
    filtered_col, timeframe = feat
    map_images(filtered_col, roi, "ET", timeframe)
    # map_images(filtered_col, roi, 'PET', timeframe)

print("completed!!!")
