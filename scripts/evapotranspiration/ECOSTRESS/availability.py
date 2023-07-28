"""Get the availability of ECOSTRESS for a layer in QGIS, number of images
for a month and also the percentage area covered by the image over the 
region for a month will be exported as CSV.
Inputs:
    - enter the year for which the availability is required
    - load the vector file onto the QGIS workspace as the script will fetch
    the boundary from the QGIS active layer
"""
import json
from pathlib import Path

import ee
import pandas as pd
from qgis.core import QgsJsonExporter
from qgis.utils import iface

ee.Initialize()

# input - enter the year (hydrological)
YEAR = 2019

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

# Define the ECOSTRESS Image Collection
s2_collection = ee.ImageCollection("users/jaltolwelllabs/ET/ecostress")

# Filter the Image Collection by the region of interest and date range
filtered_collection = s2_collection.filterBounds(roi).filterDate(START_DATE, END_DATE)
print(f"total images found for the region: {filtered_collection.size().getInfo()}")

# Total area of the ROI
total_area = roi.geometry().area()


def countImagesAndCoverage(month: ee.Number) -> ee.Feature:
    """Function to calculate the number of images per month and percentage coverage

    Args:
        month (ee.Number): Month as int

    Returns:
        ee.Feature: Null geometry feature with count and percentage coverage
    """
    # Filter images for the specified month and mosaic
    images_for_month = filtered_collection.filter(
        ee.Filter.calendarRange(month, month, "month")
    )

    def process(images_for_month):
        image = images_for_month.median().select(0)

        # process the image and get the area of ROI covered with pixels
        process_image = image.gte(0).updateMask(image.gte(0)).clip(roi)
        area_image = process_image.multiply(ee.Image.pixelArea())
        area_covered = area_image.reduceRegion(
            reducer=ee.Reducer.sum(), geometry=roi.geometry(), scale=70, maxPixels=1e12
        )
        # calculate the percentage of ROI covered by the Image
        percentage_coverage = (
            ee.Number(area_covered.get("b1")).divide(total_area).multiply(100)
        )

        # Get the count of images for the month
        count = images_for_month.size()

        return ee.Feature(
            None,
            {
                "Month": month,
                "Number of Images": count,
                "Percentage Coverage (%)": percentage_coverage,
            },
        )

    def zero():
        return ee.Feature(
            None,
            {
                "Month": month,
                "Number of Images": 0,
                "Percentage Coverage (%)": 0,
            },
        )

    return ee.Algorithms.If(
        ee.Algorithms.IsEqual(images_for_month.size(), 0),
        zero(),
        process(images_for_month),
    )


# Get the distinct months in the collection
months = ee.List.sequence(1, 12)

# Map over the list of months to get the count of images and coverage for each month
monthly_image_coverage = ee.FeatureCollection(months.map(countImagesAndCoverage))

# Convert the Earth Engine FeatureCollection to a Pandas DataFrame
fetched = {
    i["properties"]["Month"]: i["properties"]
    for i in monthly_image_coverage.getInfo()["features"]
}
df = pd.DataFrame(fetched).T
df["Month"] = (
    df["Month"]
    .astype(int)
    .apply(lambda x: f"{YEAR}-{x:02d}" if x > 5 else f"{YEAR+1}-{x:02d}")
)
df.sort_values(by=["Month"], inplace=True)

# Export the DataFrame to a CSV file
df.to_csv(out_file, index=False)
print(f"output: {out_file}")
