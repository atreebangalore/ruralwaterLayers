"""
Calculate monthly Effective Precipitation as per FAO guidelines,
The Script requires daily IMD Rainfall tif,
so sequential order of execution is,
1)IMDHistoricalGrid.py
2)IMDHistoricalGrid2Tif.py
3)IMDHistoricalTif2Daily.py
4)effPrecipitation.py
"""

import rasterio
import sys
from pathlib import Path
import numpy as np
import datetime as dt
from datetime import timedelta as td

var_type = 'rain'
start_yr = int(sys.argv[1])
end_yr = int(sys.argv[2])

dataFol = Path.home().joinpath('Data', 'imd', var_type, 'tif')
outPath = dataFol.joinpath('eff_precipitation')
outPath.mkdir(parents=True, exist_ok=True)
monthOut = outPath.joinpath('monthly')
monthOut.mkdir(parents=True, exist_ok=True)


def calculation(image):
    """Effective Precipitation Calculation from IMD Precipitation
    as per FAO (https://www.fao.org/3/s2022e/s2022e08.htm)

    Args:
        image (ndArray): monthly ndArray Precipitation imagery.

    Returns:
        ndArray Effective Precipitation imagery.
    """
    image = np.where(image < 75, ((.6*image)-10), ((.8*image)-25))
    image = np.where(image < 0, 0, image)
    return image


def summation(matches):
    """Sums the input daily IMD images into a single imagery.

    Args:
        matches (list): list of paths for images to be summed.
    """
    sum = None
    for file in matches:
        if file.endswith('.tif'):
            dataset = rasterio.open(file)
            month = dataset.read(1)
            out_meta = dataset.meta

            if sum is None:
                sum = month
            else:
                sum += month
            dataset.close()
    return sum, out_meta

def saving(sum_tifpath, out_meta, sum):
    """save the sum data into tif file

    Args:
        sum_tifpath (path): path of the output file
        out_meta (dict): dictionary of metadata of tif
        sum (rasterio): sum values of the raster
    """
    with rasterio.open(sum_tifpath, "w", **out_meta) as dest:
        dest.write(sum, 1)
    print('output: ', sum_tifpath)


def main():
    """Calculate monthly effective precipitation from daily IMD precipitation.

    usage:
    python Code/atree/scripts/rainfall/effPrecipitation.py [start_yr] [end_yr]

    args:
    start_yr: start year can be between 1901 and 2020
    end_yr: end year can be between 1901 and 2020

    example:
    python Code/atree/scripts/rainfall/effPrecipitation.py 2020 2021

    output:
    monthly effective precipitation imagery at,
    {Home Dir}/Data/imd/{var_type}/tif/eff_precipitation/monthly
    """
    difference = end_yr - start_yr
    for iter in range(difference+1):
        # dictionary with month as keys and empty list as values
        monthdict = {f"{item:02d}": [] for item in range(1, 13)}
        monthTifPath = monthOut.joinpath(str(start_yr+iter))
        monthTifPath.mkdir(parents=True, exist_ok=True)
        searchDir = dataFol.joinpath(str(start_yr+iter)) # Daily tif images
        start = dt.datetime((start_yr+iter), 1, 1, 0, 0)
        end = dt.datetime((start_yr+iter), 12, 31, 0, 0)
        # append paths of images to list of corresponding month in dictionary
        for x in range(0, (end-start).days+1):
            monthdict[(start+td(days=x)).strftime("%m")].append(
                str(searchDir.joinpath((start+td(days=x)).strftime("%Y%m%d")+'.tif')))
        for month in monthdict.keys():
            # fetch list of paths of images specific to the month
            matches = monthdict[month]
            sum,out_meta=summation(matches)
            Pe = calculation(sum)
            sum_tifpath = monthTifPath.joinpath(
                str(start_yr+iter)+month+".tif")
            saving(sum_tifpath,out_meta,Pe)


if __name__ == '__main__':
    main()
