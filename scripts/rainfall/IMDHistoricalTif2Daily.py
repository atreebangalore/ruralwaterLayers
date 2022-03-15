"""
Extracts the bands of annual tif imagery
into individual daily tif imagery
"""
import sys
from pathlib import Path
import rasterio
import tif
import datetime
import numpy as np
import pandas as pd

dataFol = Path.home().joinpath('Data','imd')  
params = tif.get_params()

def write_band(output_filepath,var_type,band,height,width):
    """writes the individual band data into seperate tif image

    Args:
        output_filepath (string): location of the output tif image
        var_type (string): rain or tmin or tmax
        band (numpy array): individual day band
        height (integer): height of the image
        width (integer): width of the image
    """
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

def split_annual_tif(var_type,start_yr,end_yr):
    """splits the annual tif into seperate daily bands and
    calls write_band to write the daily band into tif imagery

    Args:
        var_type (string): rain or tmin or tmax
        start_yr (integer): year provided as arg to script
        end_yr (integer): year provided as arg to script
    """
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
    """splits the annual image into daily images
    
    Args:
    var_type (string): rain or tmin or tmax
    start_yr (string): starting year YYYY
    end_yr (string): ending year YYYY
    
    Example:
    python Code/atree/scripts/rainfall/IMDHistoricalTif2Daily.py rain 2018 2019
    
    Output:
    individual daily tif imagery at {Home Dir}/Data/imd/rain/tif/{year}/YYYYMMDD.tif
    """
    var_type = sys.argv[1]
    start_yr = int(sys.argv[2])
    end_yr = int(sys.argv[3])
    
    li = split_annual_tif(var_type,start_yr,end_yr)

if __name__=='__main__':
    main()