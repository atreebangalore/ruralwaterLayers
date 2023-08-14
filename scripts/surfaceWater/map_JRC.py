import json

import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface

ee.Initialize()

# input - enter the year (hydrological)
START_DATE = '2019-10-01'
END_DATE = '2020-01-31'

# Boundary will be automatically fetched from the QGIS active layer
active_lyr = iface.activeLayer()
lyr_name = active_lyr.name()
lyr = QgsJsonExporter(active_lyr)
gs = lyr.exportFeatures(active_lyr.getFeatures())
gj = json.loads(gs)
for feature in gj["features"]:
    feature["id"] = f'{feature["id"]:04d}'
roi = ee.FeatureCollection(gj)

jrc = ee.ImageCollection("JRC/GSW1_4/MonthlyHistory")
filtered = jrc.filterBounds(roi).filterDate(START_DATE, END_DATE)
print(f'images acquired for the Earlier year: {filtered.size().getInfo()}')

image = filtered.map(lambda x:x.eq(2)).sum().gt(0).clip(roi)

viz = ['white', 'blue']
Map.addLayer(image, {'min': 0, 'max': 1, 'palette': viz}, 'JRC_SW')
