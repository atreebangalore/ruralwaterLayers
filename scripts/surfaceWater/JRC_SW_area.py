import json
from pathlib import Path

import ee
import pandas as pd
from qgis.core import QgsJsonExporter
from qgis.utils import iface

ee.Initialize()

# input - enter the year (hydrological)
START_YEAR = 2020
END_YEAR = 2021

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
dataFol = Path.home().joinpath("Data", "surfacewater", "jrc")
dataFol.mkdir(parents=True, exist_ok=True)
out_file = dataFol.joinpath(f"{lyr_name}-{START_YEAR}-{END_YEAR}.csv")
print(f"layer to ee: {lyr_name}")

START_DATE = f"{START_YEAR}-01-01"
END_DATE = f"{END_YEAR}-12-31"

jrc = ee.ImageCollection("JRC/GSW1_4/MonthlyHistory")
filtered = jrc.filterBounds(roi).filterDate(START_DATE, END_DATE)
print(f'No. of Images: {filtered.size().getInfo()}')

out_dict = {lyr_name: {}}
for year in range(START_YEAR, END_YEAR+1):
    image = filtered.filterDate(f'{year}-01-01', f'{year}-12-31').map(lambda x:x.eq(2)).sum()
    area_image = image.multiply(ee.Image.pixelArea())
    area = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=roi.geometry(),
        scale=30,
        maxPixels=1e12,
    )
    out_dict[lyr_name][year] = round(area.get('water').getInfo(),2)

df = pd.DataFrame(out_dict)
df.to_csv(out_file)
print(f"output: {out_file}")
print("completed!!!")
