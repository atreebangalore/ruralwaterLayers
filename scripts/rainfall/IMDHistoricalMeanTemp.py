""" Calculates mean Temperature from Daily IMD min and max Temperature tif
This script utilises the output of IMDHistoricalTif2Daily.py daily Temp imagery,
so it is mandatory to run the following for both 'tmin' and 'tmax' before
executing this script.
1) IMDHistoricalGrid.py
2) IMDHistoricalGrid2Tif.py
3) IMDHistoricalTif2Daily.py
"""
import rasterio
import sys
from pathlib import Path
import datetime as dt
from datetime import timedelta as td

start_yr = int(sys.argv[1])
end_yr = int(sys.argv[2])

maxFol = Path.home().joinpath('Data', 'imd', 'tmax', 'tif')
minFol = Path.home().joinpath('Data', 'imd', 'tmin', 'tif')
outPath = Path.home().joinpath('Data', 'imd', 'tmean')
outPath.mkdir(parents=True, exist_ok=True)
dailyOut = outPath.joinpath('daily')
dailyOut.mkdir(parents=True, exist_ok=True)
monthOut = outPath.joinpath('monthly')
monthOut.mkdir(parents=True, exist_ok=True)

def meanCalcDaily(filePathList):
    """Calculation of mean for the input imagery list

    Args:
        filePathList (list): list of imagery paths for mean calculation

    Returns:
        mean, meta: mean and metadata of the input images
    """
    sum = None
    n=len(filePathList)
    for file in filePathList:
        dataset = rasterio.open(file)
        month = dataset.read(1)
        out_meta = dataset.meta

        if sum is None:
            sum = month
        else:
            sum += month
    mean = sum/n
    return mean, out_meta

def saving(tifpath, out_meta, mean):
    """save the sum data into tif file
    Args:
        tifpath (string): path of the output file
        out_meta (dict): dictionary of metadata of tif
        mean (rasterio): sum values of the raster
    """
    with rasterio.open(tifpath, "w", **out_meta) as dest:
        dest.write(mean, 1)

def main():
    """Calculate mean Temperature (daily & monthly) from daily IMD max & min Temp.
    
    usage:
    python Code/atree/scripts/rainfall/IMDHistoricalMeanTemp.py [start_yr] [end_yr]
    
    args:
    start_yr: start year can be between 1951 and current year
    end_yr: end year can be between 1951 and current year
    
    example:
    python Code/atree/scripts/rainfall/IMDHistoricalMeanTemp.py 2020 2021
    
    output:
    monthly effective precipitation imagery at,
    {Home Dir}/Data/imd/tmean/daily
    {Home Dir}/Data/imd/tmean/monthly
    """
    difference = end_yr - start_yr
    for iter in range(difference+1):
        start = dt.datetime((start_yr+iter), 1, 1, 0, 0)
        end = dt.datetime((start_yr+iter), 12, 31, 0, 0)
        # list of all dates between start and end
        allDates = ((start+td(days=x)).strftime("%Y%m%d")
                    for x in range(0, (end-start).days+1))
        dailyOutPath = dailyOut.joinpath(str(start_yr+iter))
        dailyOutPath.mkdir(parents=True,exist_ok=True)
        for date in allDates:
            # fetch particular date max and min tif image
            maxFile = str(maxFol.joinpath(str(start_yr+iter),date+'.tif'))
            minFile = str(minFol.joinpath(str(start_yr+iter),date+'.tif'))
            # calculate mean for particular date
            mean, out_meta = meanCalcDaily([maxFile,minFile])
            tifpath = str(dailyOutPath.joinpath(date+'.tif'))
            saving(tifpath,out_meta,mean)
        print('output: '+str(dailyOutPath))
        # dictionary with month as keys and empty list as values
        monthdict = {f"{item:02d}": [] for item in range(1, 13)}
        # append paths of images to list for corresponding month in dictionary
        for x in range(0, (end-start).days+1):
            monthdict[(start+td(days=x)).strftime("%m")].append(
                str(dailyOutPath.joinpath((start+td(days=x)).strftime("%Y%m%d")+'.tif')))
        monthOutPath = monthOut.joinpath(str(start_yr+iter))
        monthOutPath.mkdir(parents=True,exist_ok=True)
        for month in monthdict.keys():
            # fetch list of paths of images specific to the month
            matches = monthdict[month]
            mean, out_meta = meanCalcDaily(matches)
            tifpath = str(monthOutPath.joinpath(str(start_yr+iter)+str(month)+'.tif'))
            saving(tifpath,out_meta,mean)
        print('output: '+str(monthOutPath))

if __name__=='__main__':
    main()