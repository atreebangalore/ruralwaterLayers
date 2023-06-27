"""Generate ECOSTRESS visualisation layer in QGIS for the given
GEE Feature in given year.
Copy paste or open the file in QGIS editor and correct the year and
change the variable "district" to required GEE Feature.
execute the script to create a ECOSTRESS layer.
"""
import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS

# Initialize Earth Engine
ee.Initialize()

# Define the Feature and Year
datameet = ee.FeatureCollection("users/jaltolwelllabs/FeatureCol/MH_KAR_TN_Jaltol")
district = datameet.filter(
    ee.Filter.And(
        ee.Filter.eq("State_N", "KARNATAKA"),
        ee.Filter.eq("Dist_N", "Shimoga"),
        ee.Filter.eq("SubDist_N", "Bhadravati"),
        ee.Filter.eq("Block_N", "Bhadravati"),
        ee.Filter.eq("VCT_N", "Hunasekatte"),
    )
)
yr = "2019"


collection = ee.ImageCollection("users/jaltolwelllabs/ET/ecostress")
yr2 = str(int(yr) + 1)

# print the number of features in the filtered result, needs to be 1.
print(district.size().getInfo())
district = district.first()
# print the village name selected.
print(district.get("VCT_N").getInfo())

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
    ).filterBounds(district.geometry())

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
        reducer=ee.Reducer.mean(), geometry=district.geometry(), scale=70
    )
    return image.setMulti(stats)


# Apply the getStats function to the image collection
collection_with_stats = composites.map(getStats)

# aggregate the monthly values into a dictionary
et_val_list = collection_with_stats.aggregate_array("b1").getInfo()
et_month_list = collection_with_stats.aggregate_array("month").getInfo()
monthly_et = dict(zip(et_month_list, et_val_list))
print(monthly_et)

# summation of monthly images to generate annual image
hyd_image = composites.sum()

# calculate minimum and maximum pixel values
max_val = round(
    hyd_image.reduceRegion(
        reducer=ee.Reducer.max(), geometry=district.geometry(), scale=70
    ).getInfo()["b1"],
    2,
)
min_val = round(
    hyd_image.reduceRegion(
        reducer=ee.Reducer.min(), geometry=district.geometry(), scale=70
    ).getInfo()["b1"],
    2,
)
print(f"visualize -> min: {min_val}, max: {max_val}")

# clip the image to the Feature boundary
clipped = hyd_image.clip(district)

# add as a layer to QGIS
viz = ["#d7191c", "#fdae61", "#ffffbf", "#abdda4", "#2b83ba"]
Map.addLayer(clipped, {"palette": viz, "min": min_val, "max": max_val}, "Ecostress")
Map.centerObject(clipped)
