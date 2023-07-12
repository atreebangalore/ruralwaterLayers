"""Generate MODIS AET/PET visualisation layer in QGIS for the given
GEE Feature in given year.
Copy paste or open the file in QGIS editor and correct the year and
change the variable "district" to required GEE Feature.
execute the script to create a AET/PET layer.
"""
import ee
from ee_plugin import Map  # requires ee plugin installed in QGIS

# Initialize Earth Engine
ee.Initialize()

# Define the Feature Collection, filter and year
datameet = ee.FeatureCollection("users/jaltolwelllabs/FeatureCol/MH_KAR_TN_Jaltol")
district = datameet.filter(
    ee.Filter.And(
        ee.Filter.eq("State_N", "KARNATAKA"),
        ee.Filter.eq("Dist_N", "Chikmagalur"),
        ee.Filter.eq("SubDist_N", "Tarikere"),
        ee.Filter.eq("Block_N", "Tarikere"),
        ee.Filter.eq("VCT_N", "Shivapura"),
    )
)
yr = "2019"  # 2020-21 will be tricky in ImageCollection selection

yr2 = str(int(yr) + 1)
# based on the year entered select an ImageCollection
if int(yr) >= 2021:
    col = ee.ImageCollection("MODIS/061/MOD16A2")
else:
    col = ee.ImageCollection("MODIS/006/MOD16A2")

# print the number of features in the filtered result, needs to be 1.
print(district.size().getInfo())
district = district.first()
# print the village name selected.
print(district.get("VCT_N").getInfo())

filtered = col.filterDate(f"{yr}-06-01", f"{yr2}-06-01").filterBounds(
    district.geometry()
)
AET_sum = filtered.select(["ET"]).sum().multiply(0.1)  # multiply scale
PET_sum = filtered.select(["PET"]).sum().multiply(0.1)
# calculate the AET/PET ratio
modis_ratio = (AET_sum.divide(PET_sum)).multiply(100)

modis_clipped = modis_ratio.clip(district)

max_val = modis_ratio.reduceRegion(
    reducer=ee.Reducer.max(), geometry=district.geometry(), scale=500
).getInfo()
min_val = modis_ratio.reduceRegion(
    reducer=ee.Reducer.min(), geometry=district.geometry(), scale=500
).getInfo()
print(f"Modis -> Max: {max_val}, min: {min_val}")

# add as a layer to QGIS
viz = ["#d7191c", "#fdae61", "#ffffbf", "#abdda4", "#2b83ba"]
Map.addLayer(
    modis_clipped, {"palette": viz, "min": min_val["ET"], "max": max_val["ET"]}, "MODIS"
)
Map.centerObject(district)

# ECOSTRESS

collection = ee.ImageCollection("users/jaltolwelllabs/ET/ecostress")

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

eco_max = ee.Number(hyd_image.reduceRegion(
    reducer=ee.Reducer.max(), geometry=district.geometry(), scale=70
).get('b1'))
eco_min = ee.Number(hyd_image.reduceRegion(
    reducer=ee.Reducer.min(), geometry=district.geometry(), scale=70
).get('b1'))
pet_max = ee.Number(PET_sum.reduceRegion(
    reducer=ee.Reducer.max(), geometry=district.geometry(), scale=500
).get('PET'))
pet_min = ee.Number(PET_sum.reduceRegion(
    reducer=ee.Reducer.min(), geometry=district.geometry(), scale=500
).get('PET'))
# convert the pixel values between 0 & 1
# hyd_numera = ee.Image(hyd_image).subtract(eco_min)
# hyd_denom = eco_max.subtract(eco_min)
# hyd_image = hyd_numera.divide(hyd_denom)
# pet_numera = ee.Image(PET_sum).subtract(pet_min)
# pet_denom = pet_max.subtract(pet_min)
# PET_sum = pet_numera.divide(pet_denom)

eco_ratio = (hyd_image.divide(PET_sum)).multiply(100)

# calculate minimum and maximum pixel values
max_val = round(
    eco_ratio.reduceRegion(
        reducer=ee.Reducer.max(), geometry=district.geometry(), scale=70
    ).getInfo()["b1"],
    2,
)
min_val = round(
    eco_ratio.reduceRegion(
        reducer=ee.Reducer.min(), geometry=district.geometry(), scale=70
    ).getInfo()["b1"],
    2,
)
print(f"ECOSTRESS -> min: {min_val}, max: {max_val}")

# clip the image to the Feature boundary
eco_clipped = eco_ratio.clip(district)

# add as a layer to QGIS
viz = ["#d7191c", "#fdae61", "#ffffbf", "#abdda4", "#2b83ba"]
Map.addLayer(eco_clipped, {"palette": viz, "min": min_val, "max": max_val}, "Ecostress")
