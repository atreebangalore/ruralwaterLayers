"""To get the percentage of Irrigation from IndiaSAT draft LULC image.

Input variables to be changed by the user in the script:
- YEAR = year (hydological)
- col_name = unique column heading of the shapefile in QGIS
- CROP_PX_LIST = pixel values to be considered for cropland
- IRRIGATION_PX_LIST = pixel values to be considered for irrigation

for cropland, the pixel values of the following labels are considered,
- cropland, single kharif, single non-kharif, double crop, triple crop
for irrigation, the pixel values of the following labels are considered,
- double crop, triple crop
"""
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple

import ee
import pandas as pd
from qgis.core import QgsJsonExporter
from qgis.utils import iface

ee.Initialize()

# input - enter the year (hydrological)
YEAR = 2016
col_name = "shrid2"
CROP_PX_LIST = [5, 9, 10, 11, 12]
IRRIGATION_PX_LIST = [11, 12]

lulc = ee.ImageCollection("users/jaltolwelllabs/LULC/IndiaSAT_phase1_draft")
START_DATE = f"{YEAR}-06-01"
END_DATE = f"{YEAR+1}-06-01"

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
dataFol = Path.home().joinpath("Data", "lulc", "irrigation")
dataFol.mkdir(parents=True, exist_ok=True)
out_file = dataFol.joinpath(f"{lyr_name}-{YEAR}.csv")
print(f"layer to ee: {lyr_name}")

filtered = lulc.filterDate(START_DATE, END_DATE).filterBounds(roi).select(["b1"])
print(f"images acquired: {filtered.size().getInfo()}")
image = filtered.mosaic()


def extract_px(image: ee.Image, px_list: List[int]) -> ee.Image:
    """extract the pixel values from the px_list into a binary image

    Args:
        image (ee.Image): Image from which the pixels to be extracted
        px_list (List[int]): list of pixel values to extract

    Returns:
        ee.Image: binary image of pixels specified having value of 1
    """
    mask = image.eq(px_list[0])
    for i in px_list[1:]:
        mask = mask.Or(image.eq(i))
    return mask


# extract the pixels into a binary image
crop_image = extract_px(image, CROP_PX_LIST)
irrig_image = extract_px(image, IRRIGATION_PX_LIST)

# extract only the pixels with value 1 and leave out the rest
crop_mask = crop_image.selfMask()
irrig_mask = irrig_image.selfMask()


def calc_info(feature: ee.Feature, image: ee.Image) -> Tuple[str, Dict[str, float]]:
    """Get the count of pixels in the image for the given feature

    Args:
        feature (ee.Feature): feature to which the count to be made
        image (ee.Image): count of pixels to be got from this image

    Returns:
        Tuple[str, Dict[str, float]]: output
    """
    dist_name = feature.getInfo()["properties"][col_name]
    params = {
        "reducer": ee.Reducer.count(),
        "geometry": feature.geometry(),
        "scale": 30,
        "maxPixels": 1e12,
    }
    classified = image.reduceRegion(**params).getInfo()
    return dist_name, classified


fc_size = roi.size().getInfo()
print(f"number of features: {fc_size}")
fc_list = roi.toList(fc_size)


def fetch_data(
    image: ee.Image, heading: str, out_dict: Dict[str, Dict[str, float]] = dict()
) -> Dict[str, Dict[str, float]]:
    """fetch the count of pixels

    Args:
        image (ee.Image): image over which the count of pixels to be extracted
        heading (str): column heading in the output
        out_dict (Dict[str, Dict[str, float]], optional): output dict from previous step. Defaults to dict().

    Returns:
        Dict[str, Dict[str, float]]: output dict
    """
    out_dict[heading] = {}
    with ThreadPoolExecutor() as ex:
        futures = [
            ex.submit(calc_info, ee.Feature(fc_list.get(num)), image)
            for num in range(fc_size)
        ]
    for future in as_completed(futures):
        name, out = future.result()
        out_dict[heading][name] = out["b1"]
    return out_dict


# fetch the count of pixels for cropland and irrigation
print("started fetching... (this takes a lot of time)")
out_dict = fetch_data(crop_mask, "cropland")
print("fetched cropland...")
out_dict = fetch_data(irrig_mask, "irrigation", out_dict)
print("fetched irrigation...")

# export to CSV
df = pd.DataFrame(out_dict)
df["percentage"] = (df["irrigation"] / df["cropland"]) * 100
df.to_csv(out_file)
print(f"output: {out_file}")
print("completed!!!")
