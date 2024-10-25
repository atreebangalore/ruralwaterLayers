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
    "#000000", # black (background)
    "#ff2d00", # red (Built-up)
    "#fff000", # yellow (water)
    "#fff000", # yellow (water)
    "#fff000", # yellow (water)
    "#ffffff", # white (no class 5)
    "#397d49", # green (trees)
    "#cebf86", # khakhi (barrenlands)
    "#8b9dc3", # light blue (single)
    "#8b9dc3", # light blue (single)
    "#222f5b", # dark blue (double)
    "#222f5b", # dark blue (triple)
    "#946b2d", # brown (shrub)
]

Map.addLayer(image, {"min": 1, "max": 12, "palette": viz}, f"IndiaSAT-{YEAR}")
