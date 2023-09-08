"""Get the ECOSTRESS Monthly ET value for a layer added to QGIS workspace.
The script should be executed in the QGIS code editor with a layer added.
Methodology:
ECOSTRESS images over the region for a month are averaged and multiplied by
the number of days in the month and the spatial values are averaged to get the
monthly ET value for the region
Inputs:
- change the year (yr) for which the monthly values for hydrological year
are required
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
yr = 2019

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
out_file = dataFol.joinpath(f"{lyr_name}-{yr}-vals.csv")
print(f"layer to ee: {lyr_name}")

# Define the ECOSTRESS Image Collection
collection = ee.ImageCollection("users/jaltolwelllabs/ET/ecostress")

yr2 = str(yr + 1)
# GENERATE LIST OF (YEAR,MONTH) TUPLES
monthseq = ["06", "07", "08", "09", "10", "11", "12", "01", "02", "03", "04", "05"]
yearseq = [yr] * 7 + [yr2] * 5
monthyearseq = [*zip(yearseq, monthseq)]
dates = [f"{year}-{month}-01" for year, month in monthyearseq]


# Function to calculate the mean composite for each month
def calculate_mean_composite(date):
    """Function to calculate the mean composite for each month.
    average of all ECOSTRESS images available in a month and
    the pixel values are multiplied by the number of days in the month.

    Args:
        date (str): Date for each month

    Returns:
        ee.Image: month image
    """
    # Convert the month number to an EE date object
    month_date = ee.Date(date)

    # Filter the collection by month
    filtered = collection.filterDate(
        month_date, month_date.advance(1, "month")
    ).filterBounds(roi.geometry())

    # Calculate the mean composite
    composite = ee.Algorithms.If(
        filtered.size() != 0, filtered.mean(), ee.Image.constant(0)
    )

    # Multiply the composite by the number of days in the month
    days_in_month = month_date.advance(1, "month").difference(month_date, "day")
    composite = ee.Image(composite).multiply(days_in_month)

    # Set a property for the composite with the month name
    composite = composite.set("month", month_date.format("MMMYYYY"))

    return composite


# Map over the list of months to calculate the mean composites
composites = ee.ImageCollection.fromImages(ee.List(dates).map(calculate_mean_composite))


def getStats(image):
    """get the spatial mean value of all pixels in an image.

    Args:
        image (ee.Image): Month Images

    Returns:
        ee.Element: Element object with mean values of band.
    """
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(), geometry=roi.geometry(), scale=70
    )
    return image.setMulti(stats)


# Apply the getStats function to the image collection
collection_with_stats = composites.map(getStats)

# aggregate the monthly values into a dictionary
et_val_list = collection_with_stats.aggregate_array("b1").getInfo()
et_month_list = collection_with_stats.aggregate_array("month").getInfo()
monthly_et = dict(zip(et_month_list, et_val_list))
print(monthly_et)

# convert the dictionary to Pandas DataFrame and save
df = pd.DataFrame(monthly_et, index=[0]).T
df.to_csv(out_file)
print(f"output: {out_file}")
