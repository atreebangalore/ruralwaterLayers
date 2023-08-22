"""visualisation of LGRIP irrigation and rainfed regions for the layer
imported into the QGIS workspace. This also generates the irrigation product of
ESA world cereal dataset for the given feature in QGIS.
execute the code in QGIS.
"""
from pathlib import Path
from typing import Any, Dict

import ee
import pandas as pd
from ee_plugin import Map  # requires ee plugin installed in QGIS

# Initialize Earth Engine
ee.Initialize()

import json

from qgis.core import QgsJsonExporter
from qgis.utils import iface

unique_field = "DISTRICT"

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
dataFol = Path.home().joinpath("Data", "ag", "lgrip")
dataFol.mkdir(parents=True, exist_ok=True)
out_file = dataFol.joinpath(f"{lyr_name}.csv")
print(f"layer to ee: {lyr_name}")

# get the ImageCollections
lgrip = ee.ImageCollection("projects/sat-io/open-datasets/GFSAD/LGRIP30")
esa_cereal = ee.ImageCollection("ESA/WorldCereal/2021/MODELS/v100")

# Filter the collection and create the image of the geometry
lgrip_filtered = lgrip.filterBounds(roi).mosaic().select(["b1"])
lgrip_image = lgrip_filtered.updateMask(lgrip_filtered.gte(2)).clip(roi)

esa_cereal = esa_cereal.filterBounds(roi).map(lambda x: x.updateMask(x.neq(0)))
esa_image = esa_cereal.filter('product == "irrigation"').mosaic().clip(roi)

# Display on the QGIS workspace
# Map.addLayer(lgrip_image, {"min": 2, "max": 3, "palette": ["blue", "yellow"]}, "lgrip")
# Map.addLayer(
#     esa_image,
#     {"max": 100, "bands": ["classification"], "palette": ["blue"]},
#     "esa_cereal",
# )


# Calculate the area of irrigation and rainfed classes in the boundary
def get_area(
    image: ee.Image, feature: ee.Feature, band_num: int, scale_val: int, band_name: str
) -> Dict[str, float]:
    """get the area for a feature and not feature collection.

    Args:
        image (ee.Image): Image from which area to tbe calculated
        feature (ee.Feature): the entire layer will be considered as feature
        band_num (int): the class pixel value
        scale_val (int): scale value
        band_name (str): name of the band

    Returns:
        Dict[str, float]: Dict from the GEE
    """
    class_image = image.eq(band_num)
    area_image = class_image.multiply(ee.Image.pixelArea())
    area = area_image.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=feature.geometry(),
        scale=scale_val,
        maxPixels=1e12,
    )
    return area.get(band_name).getInfo()


# print(f'LGRIP irrigated area: {get_area(lgrip_image, roi, 2, 30, "b1")}')
# print(f'LGRIP rainfed area: {get_area(lgrip_image, roi, 3, 30, "b1")}')
# print(
#     f'ESA WorldCereal irrigated area: {get_area(esa_image, roi, 100, 10, "classification")}'
# )


def feature_stats(
    image: ee.Image, fc: ee.FeatureCollection, class_num: int, scale_val: int
) -> Dict[str, Any]:
    """Get the area for each feature in the feature collection

    Args:
        image (ee.Image): image from which area to be calculated
        fc (ee.FeatureCollection): QGIS layer as feature collection
        class_num (int): the class pixel value
        scale_val (int): scale value

    Returns:
        Dict[str, Any]: Dict from GEE
    """
    class_image = image.eq(class_num)
    area_image = class_image.multiply(ee.Image.pixelArea())
    area = area_image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.sum(),
        scale=scale_val,
        crs="EPSG:4326",
    )
    return area.getInfo()


irrig_stats = feature_stats(lgrip_image, roi, 2, 30)
rainfed_stats = feature_stats(lgrip_image, roi, 3, 30)

# process the GEE output as a single dict to become DataFrame
out_dict = {}
for f in irrig_stats["features"]:
    stat = f["properties"]
    out_dict[stat[unique_field]] = {"irrig(ha)": round((stat["sum"] / 1e4), 2)}
for f in rainfed_stats["features"]:
    stat = f["properties"]
    out_dict[stat[unique_field]]["rainfed(ha)"] = round((stat["sum"] / 1e4), 2)

# conver to DataFrame and save
df = pd.DataFrame(out_dict).T
df.to_csv(out_file)

print(f"output: {out_file}")
print("completed!")
