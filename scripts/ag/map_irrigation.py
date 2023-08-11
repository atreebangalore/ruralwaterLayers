"""visualisation of LGRIP irrigation and rainfed regions for the layer
imported into the QGIS workspace. This also generates the irrigation product of
ESA world cereal dataset for the given feature in QGIS.
execute the code in QGIS.
"""
import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS

# Initialize Earth Engine
ee.Initialize()

import json

from qgis.core import QgsJsonExporter
from qgis.utils import iface

# Boundary will be automatically fetched from the QGIS active layer
active_lyr = iface.activeLayer()
lyr_name = active_lyr.name()
lyr = QgsJsonExporter(active_lyr)
gs = lyr.exportFeatures(active_lyr.getFeatures())
gj = json.loads(gs)
for feature in gj["features"]:
    feature["id"] = f'{feature["id"]:04d}'
roi = ee.FeatureCollection(gj)

# get the ImageCollections
lgrip = ee.ImageCollection("projects/sat-io/open-datasets/GFSAD/LGRIP30")
esa_cereal = ee.ImageCollection("ESA/WorldCereal/2021/MODELS/v100")

# Filter the collection and create the image of the geometry
lgrip_filtered = lgrip.filterBounds(roi).mosaic().select(["b1"])
lgrip_image = lgrip_filtered.updateMask(lgrip_filtered.gte(2)).clip(roi)

esa_cereal = esa_cereal.filterBounds(roi).map(lambda x: x.updateMask(x.neq(0)))
esa_image = esa_cereal.filter('product == "irrigation"').mosaic().clip(roi)

# Display on the QGIS workspace
Map.addLayer(lgrip_image, {"min": 2, "max": 3, "palette": ["blue", "yellow"]}, "lgrip")
Map.addLayer(
    esa_image,
    {"max": 100, "bands": ["classification"], "palette": ["blue"]},
    "esa_cereal",
)


# Calculate the area of irrigation and rainfed classes in the boundary
def get_area(image, feature, band_num, scale_val, band_name):
    class_image = image.eq(band_num)
    area_image = class_image.multiply(ee.Image.pixelArea())
    area = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=feature.geometry(),
        scale=scale_val,
        maxPixels=1e12,
    )
    return area.get(band_name).getInfo()


print(f'LGRIP irrigated area: {get_area(lgrip_image, roi, 2, 30, "b1")}')
print(f'LGRIP rainfed area: {get_area(lgrip_image, roi, 3, 30, "b1")}')
print(
    f'ESA WorldCereal irrigated area: {get_area(esa_image, roi, 100, 10, "classification")}'
)

print("completed!")
