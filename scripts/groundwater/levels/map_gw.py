import json
from pathlib import Path

import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
import pandas as pd
from qgis.core import QgsJsonExporter
from qgis.utils import iface

ee.Initialize()

YEAR = 2000

# Boundary will be automatically fetched from the QGIS active layer
active_lyr = iface.activeLayer()
lyr_name = active_lyr.name()
lyr = QgsJsonExporter(active_lyr)
gs = lyr.exportFeatures(active_lyr.getFeatures())
gj = json.loads(gs)
for feature in gj["features"]:
    feature["id"] = f'{feature["id"]:04d}'
roi = ee.FeatureCollection(gj)

# Output location and file name to save
dataFol = Path.home().joinpath("Data", "et", "ecostress")
dataFol.mkdir(parents=True, exist_ok=True)
out_file = dataFol.joinpath(f"{lyr_name}-{YEAR}.csv")
print(f"layer to ee: {lyr_name}")

START_DATE = f"{YEAR}-06-01"
END_DATE = f"{YEAR+1}-06-01"

gw_col = ee.ImageCollection('users/jaltolwelllabs/GW/IndiaWRIS_IN')
filtered = gw_col.filterBounds(roi).filterDate(START_DATE, END_DATE)
print(f'No. of Images: {filtered.size().getInfo()}')

image = filtered.mean()

# calculate minimum and maximum pixel values
max_val = round(
    image.reduceRegion(
        reducer=ee.Reducer.max(), geometry=roi.geometry(), scale=70
    ).getInfo()["b1"],
    2,
)
min_val = round(
    image.reduceRegion(
        reducer=ee.Reducer.min(), geometry=roi.geometry(), scale=70
    ).getInfo()["b1"],
    2,
)
print(f"visualize -> min: {min_val}, max: {max_val}")

clipped = image.clip(roi)

Map.addLayer(clipped, {'min': min_val, 'max': max_val, 'palette':['#CAD5E2', 'black']}, f'GW-{YEAR}')
