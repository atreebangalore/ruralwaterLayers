"""
Calculate Reference Crop ET as per FAO
This script requires p-value from pAnnualDaytimeHrs.py and
mean Temperature from IMDHistoricalMeanTemp.py which in-turn requires
max and min IMD Temperature Imagery.

https://www.fao.org/3/s2022e/s2022e07.htm#3.1.3%20blaney%20criddle%20method
"""
from numpy import diff
import rasterio
import sys
from pathlib import Path

start_yr = int(sys.argv[1])
end_yr = int(sys.argv[2])

meanPath = Path.home().joinpath('Data', 'imd', 'tmean', 'monthly')
pValuePath = Path.home().joinpath('Data', 'et', 'fao', 'p_value')
outPath = Path.home().joinpath('Data', 'et', 'fao', 'refCropET')
outPath.mkdir(parents=True, exist_ok=True)

def EToCalc(meanTempPath, pPath):
    """Calculation of reference crop ET

    Args:
        meanTempPath (string): path to the specific month mean Temp Image
        pPath (string): path to the specific month p-value image

    Returns:
        Array: reference crop ET
        Dict: metadata of imagery
    """
    with rasterio.open(meanTempPath, "r") as img:
        meanTemp = img.read(1)
        out_meta = img.meta
    with rasterio.open(pPath, "r") as img:
        pImage = img.read(1)
    refET = pImage*((0.46*meanTemp)+8)
    return refET, out_meta

def main():
    """Calculation of Reference Crop ET from Annual Daytime Hours and mean Temp
    
    Usage:
    python Code/atree/scripts/evapotranspiration/fao/refCropET.py [start_yr] [end_yr]
    
    Args:
    start_yr : Starting year
    end_yr : Ending year
    
    Example:
    python Code/atree/scripts/evapotranspiration/fao/refCropET.py 2018 2019
    
    Output:
    {Home Dir}/Data/et/fao/refCropET/{year}
    """
    difference = end_yr - start_yr
    monthGen = [f"{item:02d}" for item in range(1, 13)]
    for iter in range(difference+1):
        year = start_yr+iter
        for month in monthGen:
            meanTempFile = meanPath.joinpath(str(year),f'{year}{month}.tif')
            pFile = pValuePath.joinpath(f'{month}.tif')
            refET, out_meta = EToCalc(meanTempFile, pFile)
            outFilePath = outPath.joinpath(str(year))
            outFilePath.mkdir(parents=True, exist_ok=True)
            outFile = outFilePath.joinpath(f'{year}{month}01.tif')
            with rasterio.open(outFile, "w", **out_meta) as dest:
                dest.write(refET, 1)
            print(f'Output : {outFile}')

if __name__=='__main__':
    main()