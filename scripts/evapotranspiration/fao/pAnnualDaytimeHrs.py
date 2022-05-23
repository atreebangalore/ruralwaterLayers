"""
MEAN DAILY PERCENTAGE (p) OF ANNUAL DAYTIME HOURS FOR DIFFERENT LATITUDES
calculated as spatial raster with reference to the FAO Blaney-Criddle method

Requires a tmax or tmin tif file from IMDHistoricalTif2Daily output as a
reference to generate the skeleton of p value tif file.

https://www.fao.org/3/s2022e/s2022e07.htm#3.1.3%20blaney%20criddle%20method
"""
import rasterio
import numpy as np
import sys
from pathlib import Path

# Args for referencing source file
var_type = sys.argv[1]
file_name = sys.argv[2]
year = file_name[:4]

# tmax or tmin tif file as source of reference
source = Path.home().joinpath("Data", "imd", var_type, "tif", year, file_name)
outPath = Path.home().joinpath("Data", "et", "fao", "p_value")
outPath.mkdir(parents=True, exist_ok=True)  # create if not exist

# p values for various latitude values (keys)
# only North values for p are considered
p_fao = {
    40.0: [0.22, 0.24, 0.27, 0.30, 0.32, 0.34, 0.33, 0.31, 0.28, 0.25, 0.22, 0.21],
    35.0: [0.23, 0.25, 0.27, 0.29, 0.31, 0.32, 0.32, 0.30, 0.28, 0.25, 0.23, 0.22],
    30.0: [0.24, 0.25, 0.27, 0.29, 0.31, 0.32, 0.31, 0.30, 0.28, 0.26, 0.24, 0.23],
    25.0: [0.24, 0.26, 0.27, 0.29, 0.30, 0.31, 0.31, 0.29, 0.28, 0.26, 0.25, 0.24],
    20.0: [0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.30, 0.29, 0.28, 0.26, 0.25, 0.25],
    15.0: [0.26, 0.26, 0.27, 0.28, 0.29, 0.29, 0.29, 0.28, 0.28, 0.27, 0.26, 0.25],
    10.0: [0.26, 0.27, 0.27, 0.28, 0.28, 0.29, 0.29, 0.28, 0.28, 0.27, 0.26, 0.26],
    5.0: [0.27, 0.27, 0.27, 0.28, 0.28, 0.28, 0.28, 0.28, 0.28, 0.27, 0.27, 0.27],
}


def getLatitude(data, getTransform):
    """get latitude of pixels from the souce image

    Args:
        data (numpy array): souce image read using rasterio
        getTransform (Affine): Affine Transform of source

    Returns:
        numpy array: latitude value of each pixels
    """
    height = data.shape[0]
    width = data.shape[1]
    cols, rows = np.meshgrid(np.arange(width), np.arange(height))
    xs, ys = rasterio.transform.xy(getTransform, rows, cols)
    return np.array(ys)


def saving(pBand, month, latBand, out_meta):
    """save the pBand and latBand into tif file

    Args:
        pBand (numpy array): p values
        month (int): month starting from 0 for Jan to 11 for Dec
        latBand (numpy arrat): latitude values
        out_meta (dict): dictionary of metadata of tif imagery
    """
    # Added 1 to month so naming becomes 01.tif for Jan and 12.tif for Dec
    month_tifpath = outPath.joinpath(f"{month+1:02d}.tif")
    out_meta.update({"count": 2})
    with rasterio.open(month_tifpath, "w", **out_meta) as dest:
        dest.write(pBand, 1)
        dest.set_band_description(1, "p")
        dest.write(latBand, 2)
        dest.set_band_description(2, "lat")
    print("output: ", month_tifpath)


def generateImage(pBand, month, latBand, out_meta):
    """Fetches p value referencing the fao dict for calculated latitude

    Args:
        pBand (numpy array): p values
        month (int): month starting from 0 for Jan to 11 for Dec
        latBand (numpy arrat): latitude values
        out_meta (dict): dictionary of metadata of tif imagery
    """
    for row in range(pBand.shape[0]):
        lat = pBand[row][0]
        if lat % 5 < 2.5:
            refLat = (lat // 5) * 5
        else:
            refLat = ((lat // 5) + 1) * 5
        pBand = np.where(pBand == lat, p_fao[refLat][month], pBand)
    saving(pBand, month, latBand, out_meta)


def main():
    """Calculates p Annual Daytime Hours (using FAO method) for latitudes
    referenced from the source IMD tif file
    
    Usage:
        python Code\atree\scripts\evapotranspiration\fao\pAnnualDaytimeHrs.py [var_type] [filename]
        
    Args:
        var_type: tmax or tmin 
        filename: filename of output from IMDHistoricalTif2Daily.csv for tmax or tmin
        (this file will be used as reference for creating p value tif)
    
    Example:
        python Code\atree\scripts\evapotranspiration\fao\pAnnualDaytimeHrs.py tmax 20150101.tif
    
    Output:
        monthly p value tif files are exported to
        {Home Dir}\Data\et\fao\p_value\
    """
    image = rasterio.open(source)
    data = image.read(1)
    out_meta = image.meta
    getTransform = image.transform
    latBand = getLatitude(data, getTransform)
    for month in range(12):
        pBand = np.copy(latBand)
        generateImage(pBand, month, latBand, out_meta)
    image.close()


if __name__ == "__main__":
    main()