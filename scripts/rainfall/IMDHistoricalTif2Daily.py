import sys
import os
from pathlib import Path
import rasterio
import tif
import datetime
import numpy as np
import pandas as pd

dataFol = Path.home().joinpath('Data','imd')  
params = tif.get_params()

def write_band(output_filepath,var_type,band,height,width):
    transform = params[var_type]['affine']
    dailyTif = rasterio.open(output_filepath,
                             'w',
                             driver='GTiff',
                             height=height,
                             width=width,
                             count=1,
                             nodata=-999,
                             dtype=np.float64,
                             crs='+proj=latlong',
                             transform=transform)
    dailyTif.write(band,1)
    dailyTif.close()

def split_annual_tif(var_type,start_yr,end_yr):    #
    ifmt = 'tif'
    li = []
    for year in range(start_yr,end_yr+1):
        input_file = '{}.tif'.format(year)
        input_filepath = dataFol.joinpath(var_type,ifmt,input_file)
        print("input filepath: ",input_filepath)
        dataset = rasterio.open(input_filepath)
        count = dataset.count
        for i in range(1,count+1):
            band = dataset.read(i)
            print("read band ",i)
            height,width = band.shape
            print("height is :",height," and width is :",width)
            date = datetime.datetime.strptime(str(year)+str(i), '%Y%j')
            print("date is :",date)
            output_file = date.strftime('%Y%m%d')+".tif"
            output_filepath = dataFol.joinpath(var_type,ifmt,str(year),output_file)
            print("output filepath: ",output_filepath)
            if not output_filepath.parent.exists():
                output_filepath.parent.mkdir()
                print("output directory created")
                write_band(output_filepath,var_type,band,height,width)          
            else:
                print("output directory already present")
                write_band(output_filepath,var_type,band,height,width)
            li.append(output_filepath)
        dataset.close()
    return li

def main():
    var_type = sys.argv[1]
    start_yr = int(sys.argv[2])
    end_yr = int(sys.argv[3])
    
    li = split_annual_tif(var_type,start_yr,end_yr)

if __name__=='__main__':
    main()