import os,sys
from pathlib import Path
import glob
import rasterio
from matplotlib import pyplot as plt
import numpy as np

dataFol = Path.home().joinpath("Data","et","sebop")
soi_boundary = Path.home().joinpath("Data","gis","soi_national_boundary.shp")


def main():
    """calculates raster sum of monthly SEBOP ET images for water year and saves to file
    """
    
    year = sys.argv[1]
    year2 = str(int(year) + 1)
    
    monthseq = ['06','07','08','09','10','11','12','01','02','03','04','05']
    yearmonseq = ['m' + year + m + "*_india.tif" for m in monthseq[0:7]] + ['m' + year2 + m + "*_india.tif" for m in monthseq[7:]]
    
#     print("monthly files to filter: ",yearmonseq,"\n")
    
    # FILTER FILES IN DATA FOLDER TO BE SUMMED
    os.chdir(str(dataFol))
    matches = []
    for pattern in yearmonseq:
        fn = glob.glob(pattern)
        matches += fn
        
#     print("tifs to be summed: ",matches)
    
    # READ IN FILES TO BE SUMMED
    sum = None
    for file in matches:
        dataset = rasterio.open(file)
        month = dataset.read(1)
        out_meta = dataset.meta
        
        if sum is None:
            sum = month
        else:
            sum += month
    
    sum = np.where(sum==0,-32768,sum)
#     print(out_meta)
    
    sum_tifpath = dataFol.joinpath("water_y" + year + "_india.tif")
    
    # WRITING SUMMED ET TO FILE
    with rasterio.open(sum_tifpath, "w", **out_meta) as dest:
        dest.write(sum,1)
        print("SEBOP Water Year Cumulative Sum image written to file: ",sum_tifpath)
    
if __name__=="__main__":
    main()