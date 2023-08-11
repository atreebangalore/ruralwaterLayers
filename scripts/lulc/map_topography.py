"""visualization of SRTM ELEVATION and the slope derived in QGIS.
The script should be executed in QGIS workspace with a layer added to it,
for which the DEM and Slope to be mapped.
"""
import json

import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS
from qgis.core import QgsJsonExporter
from qgis.utils import iface

ee.Initialize()

# Boundary will be automatically fetched from the QGIS active layer
active_lyr = iface.activeLayer()
lyr_name = active_lyr.name()
lyr = QgsJsonExporter(active_lyr)
gs = lyr.exportFeatures(active_lyr.getFeatures())
gj = json.loads(gs)
for feature in gj["features"]:
    feature["id"] = f'{feature["id"]:04d}'
roi = ee.FeatureCollection(gj)

# SRTM elevation image and slope calculation
srtm = ee.Image("CGIAR/SRTM90_V4")
srtm_slope = ee.Terrain.slope(srtm)

# calculate minimum and maximum pixel values
dem_max_val = round(
    srtm.reduceRegion(
        reducer=ee.Reducer.max(), geometry=roi.geometry(), scale=90
    ).getInfo()["elevation"],
    2,
)
dem_min_val = round(
    srtm.reduceRegion(
        reducer=ee.Reducer.min(), geometry=roi.geometry(), scale=90
    ).getInfo()["elevation"],
    2,
)
slope_max_val = round(
    srtm_slope.reduceRegion(
        reducer=ee.Reducer.max(), geometry=roi.geometry(), scale=90
    ).getInfo()["slope"],
    2,
)
slope_min_val = round(
    srtm_slope.reduceRegion(
        reducer=ee.Reducer.min(), geometry=roi.geometry(), scale=90
    ).getInfo()["slope"],
    2,
)
print(f"DEM visualize -> min: {dem_min_val}, max: {dem_max_val}")
print(f"Slope visualize -> min: {slope_min_val}, max: {slope_max_val}")

# clip the image
dem = srtm.clip(roi)
slope = srtm_slope.clip(roi)

# add as layer to the QGIS workspace
viz = ["#d7191c", "#fdae61", "#ffffbf", "#abdda4", "#2b83ba"]
Map.addLayer(dem, {"palette": viz, "min": dem_min_val, "max": dem_max_val}, "dem")
Map.addLayer(
    slope, {"palette": viz, "min": slope_min_val, "max": slope_max_val}, "slope"
)
Map.centerObject(dem)
