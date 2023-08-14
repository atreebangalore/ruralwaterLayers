import json

import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface

ee.Initialize()

# input - enter the year (hydrological)
EARLIER_YEAR = 2000
LATEST_YEAR = 2020

# Boundary will be automatically fetched from the QGIS active layer
active_lyr = iface.activeLayer()
lyr_name = active_lyr.name()
lyr = QgsJsonExporter(active_lyr)
gs = lyr.exportFeatures(active_lyr.getFeatures())
gj = json.loads(gs)
for feature in gj["features"]:
    feature["id"] = f'{feature["id"]:04d}'
roi = ee.FeatureCollection(gj)

EARLIER_START_DATE = f"{EARLIER_YEAR}-06-01"
EARLIER_END_DATE = f"{EARLIER_YEAR+1}-06-01"

LATEST_START_DATE = f"{LATEST_YEAR}-06-01"
LATEST_END_DATE = f"{LATEST_YEAR+1}-06-01"

jrc = ee.ImageCollection("JRC/GSW1_4/MonthlyHistory")
e_filtered = jrc.filterBounds(roi).filterDate(EARLIER_START_DATE, EARLIER_END_DATE)
l_filtered = jrc.filterBounds(roi).filterDate(LATEST_START_DATE, LATEST_END_DATE)
print(f'images acquired for the Earlier year: {e_filtered.size().getInfo()}')
print(f'images acquired for the Latest year: {l_filtered.size().getInfo()}')

e_image = e_filtered.map(lambda x:x.eq(2)).sum().gt(0)
l_image = l_filtered.map(lambda x:x.eq(2)).sum().gt(0)

permanent = ((e_image.add(l_image)).eq(2)).multiply(2)
difference = (l_image.subtract(e_image))
increase = (difference.eq(1)).multiply(3)
decrease = difference.eq(-1)

out = permanent.add(increase).add(decrease).clip(roi)

viz = ['white', 'red', 'blue', 'green']
Map.addLayer(out, {'min': 0, 'max': 3, 'palette': viz}, 'JRC_diff')
# Map.centerObject(out)