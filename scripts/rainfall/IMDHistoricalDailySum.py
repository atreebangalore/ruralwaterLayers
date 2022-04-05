"""
Summation of Daily IMD tif into Monthly, Yearly or Water Year
"""

import rasterio, sys, os
from pathlib import Path
import glob

var_type = sys.argv[1]
start_yr = int(sys.argv[2])
end_yr = int(sys.argv[3])
period = sys.argv[4]

dataFol = Path.home().joinpath('Data','imd',var_type,'tif')
outPath = dataFol.joinpath('period')
outPath.mkdir(parents=True, exist_ok=True)

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
    return sum,out_meta

def matching(mfn,searchDir):
    """finds the path of files with matching pattern

    Args:
        mfn (string): pattern for matching
        searchDir (path): path to search for files

    Returns:
        list: list of absolute paths of matching files
    """
    os.chdir(str(searchDir))
    matches = []
    for pattern in mfn:
        fn = glob.glob(pattern)
        matches += fn
    matches=[str(searchDir.joinpath(item)) for item in matches]
    os.chdir(str(Path.home()))
    return matches

def saving(sum_tifpath,out_meta,sum):
    """save the sum data into tif file

    Args:
        sum_tifpath (path): path of the output file
        out_meta (dict): dictionary of metadata of tif
        sum (rasterio): sum values of the raster
    """
    with rasterio.open(sum_tifpath, "w", **out_meta) as dest:
        dest.write(sum,1)
    print('output: ',sum_tifpath)

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
    difference = end_yr - start_yr
    for iter in range(difference+1):
        if period == 'annual':
            yearlyfn = str(start_yr+iter) + "*.tif"
            searchDir=dataFol.joinpath(str(start_yr+iter))
            matches = matching(yearlyfn,searchDir)
            sum,out_meta=summation(matches)
            sum_tifpath = outPath.joinpath("yr_"+str(start_yr+iter)+"_india.tif")
            saving(sum_tifpath,out_meta,sum)
        elif period == 'wateryr':
            if difference!=0:
                if iter<difference:
                    monthseq = ['06','07','08','09','10','11','12','01','02','03','04','05']
                    yearseq = [start_yr+iter]*7 + [start_yr+iter+1]*5 
                    monthyearseq = [*zip(yearseq,monthseq)]    # (2003,06), (2003,07), ..
                    monthlyfn = [str(year) + str(month) + "*.tif" for year,month in monthyearseq]
                    searchDir=dataFol.joinpath(str(start_yr+iter))
                    matches1 = matching(monthlyfn,searchDir)
                    searchDir=dataFol.joinpath(str(start_yr+iter+1))
                    matches2 = matching(monthlyfn,searchDir)
                    matches=matches1+matches2
                    sum,out_meta=summation(matches)
                    sum_tifpath = outPath.joinpath("wy"+str(start_yr+iter)+"_india.tif")
                    saving(sum_tifpath,out_meta,sum)
            else:
                sys.exit('start_yr and end_yr cannot be same for wateryr.')
        elif period == 'monthly':
            monthseq = [f"{item:02d}" for item in range(1,13)]
            for month in monthseq:
                monthlyfn = str(start_yr+iter) + month + "*.tif"
                searchDir=dataFol.joinpath(str(start_yr+iter))
                matches = matching(monthlyfn,searchDir)
                sum,out_meta=summation(matches)
                sum_tifpath = outPath.joinpath(str(start_yr+iter)+month+"_india.tif")
                saving(sum_tifpath,out_meta,sum)
        else:
            sys.exit('The period for calculation is invalid\n\
                please mention "annual" or "wateryr" or "monthly" correctly')

if __name__=='__main__':
    main()