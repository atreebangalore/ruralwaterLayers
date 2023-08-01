"""Visualize Draft IndiaSAT LULC image in QGIS for given year
"""
import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS

ee.Initialize()

# input - enter the year (hydrological)
YEAR = 2021

START_DATE = f"{YEAR}-06-01"
END_DATE = f"{YEAR+1}-06-01"

lulc = ee.ImageCollection("users/jaltolwelllabs/LULC/IndiaSAT_phase1_draft")
filtered = lulc.filterDate(START_DATE, END_DATE).select(["b1"])
image = filtered.mosaic()

viz = [
    "#b2df8a",
    "#6382ff",
    "#d7191c",
    "#f5ff8b",
    "#dcaa68",
    "#33a02c",
    "#50c361",
    "#000000",
    "#dac190",
    "#a6cee3",
    "#38c5f9",
    "#6e0002",
]

Map.addLayer(image, {"min": 1, "max": 12, "palette": viz}, f"IndiaSAT-{YEAR}")
