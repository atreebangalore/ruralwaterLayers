"""
Summation of Daily IMD tif into Monthly, Yearly or Water Year
The Script requires daily IMD Rainfall tif from IMDHistoricalTif2Daily.py
"""

import rasterio
import sys
from pathlib import Path
import datetime as dt
from datetime import timedelta as td

var_type = sys.argv[1]
start_yr = int(sys.argv[2])
end_yr = int(sys.argv[3])
period = sys.argv[4]

dataFol = Path.home().joinpath('Data', 'imd', var_type, 'tif')
outPath = dataFol.joinpath('period')
outPath.mkdir(parents=True, exist_ok=True)  # create if not exist


def summation(matches):
    """Sums the input daily IMD images into a single imagery.

    Args:
        matches (list): list of images to be summed.
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
    """sum the daily tif into annual or monthly or wateryr

    usage:
    python Code/atree/scripts/rainfall/IMDHistoricalDailySum.py [var_type] [start_yr] [end_yr] [period]

    args:
    var_type: rain or tmin or tmax
    start_yr: for rain, between 1901 and 2020, for tmax/tmin, between 1951 and 2020
    end_yr: for rain, between 1901 and 2020, for tmax/tmin, between 1951 and 2020
    period: annual or monthly or wateryr
    (wateryr is from june 1st of start_yr to may 31st of end_yr)

    example:
    python Code/atree/scripts/rainfall/IMDHistoricalDailySum.py rain 2020 2021 annual

    output:
    {Home Dir}/Data/imd/{var_type}/tif/period
    """
    difference = end_yr - start_yr  # to calc all years between
    for iter in range(difference+1):
        searchDir = dataFol.joinpath(str(start_yr+iter))  # daily tif directory
        if period == 'annual':
            start = dt.datetime((start_yr+iter), 1, 1, 0, 0)
            end = dt.datetime((start_yr+iter), 12, 31, 0, 0)
            # list of paths for all daily images between start and end
            matches = [str(searchDir.joinpath((start+td(days=x)).strftime("%Y%m%d")+'.tif'))
                       for x in range(0, (end-start).days+1)]
            sum, out_meta = summation(matches)
            sum_tifpath = outPath.joinpath(
                "yr_"+str(start_yr+iter)+"_india.tif")
            saving(sum_tifpath, out_meta, sum)
        elif period == 'wateryr':
            if difference != 0:
                if iter < difference:
                    # hydrological year from june of first year to may of second
                    start = dt.datetime((start_yr+iter), 6, 1, 0, 0)
                    end = dt.datetime((start_yr+iter), 12, 31, 0, 0)
                    # list of paths for daily images of second half of first year
                    matches1 = [str(searchDir.joinpath(
                        (start+td(days=x)).strftime("%Y%m%d")+'.tif')) for x in range(0, (end-start).days+1)]
                    start = dt.datetime((start_yr+iter+1), 1, 1, 0, 0)
                    end = dt.datetime((start_yr+iter+1), 5, 31, 0, 0)
                    # directory for second year images
                    searchDir = dataFol.joinpath(str(start_yr+iter+1))
                    # list of paths for daily images of first half of second year
                    matches2 = [str(searchDir.joinpath(
                        (start+td(days=x)).strftime("%Y%m%d")+'.tif')) for x in range(0, (end-start).days+1)]
                    # combine lists of paths from june to may - water year
                    matches = matches1+matches2
                    sum, out_meta = summation(matches)
                    sum_tifpath = outPath.joinpath(
                        "wy"+str(start_yr+iter)+"_india.tif")
                    saving(sum_tifpath, out_meta, sum)
            else:
                sys.exit('start_yr and end_yr cannot be same for wateryr.')
        elif period == 'monthly':
            # dictionary with month as keys and empty list as values
            monthdict = {f"{item:02d}": [] for item in range(1, 13)}
            start = dt.datetime((start_yr+iter), 1, 1, 0, 0)
            end = dt.datetime((start_yr+iter), 12, 31, 0, 0)
            # append paths of images to list of corresponding month in dictionary
            for x in range(0, (end-start).days+1):
                monthdict[(start+td(days=x)).strftime("%m")].append(
                    str(searchDir.joinpath((start+td(days=x)).strftime("%Y%m%d")+'.tif')))
            for month in monthdict.keys():
                # fetch list of paths of images specific to the month
                matches = monthdict[month]
                sum, out_meta = summation(matches)
                sum_tifpath = outPath.joinpath(
                    str(start_yr+iter)+month+"_india.tif")
                saving(sum_tifpath, out_meta, sum)
        else:
            sys.exit(
                'The period for calculation is invalid\
                    \nplease mention "annual" or "wateryr" or "monthly" correctly')

if __name__ == '__main__':
    main()
