"""
Conversion of grd data aquired from IMD for Precipitation or
Min Temp or Max Temp into tif imagery
"""
import sys
from pathlib import Path
import imdlib as imd
import calendar
import rasterio
import numpy as np
import tif

dataFol = Path.home().joinpath('Data','imd')  
params = tif.get_params()


def read_convert_write(year, input_folder, var_type, output_filepath):
    """Function splits every day data in gridded format into 
    bands of tif imagery using the imdlib module

    Args:
        year (integer): year of the IMD grd data
        input_folder (string): location of grd data
        var_type (string): rain or tmin or tmax
        output_filepath (string): location for output tif imagery
    """
    file_format = 'yearwise'
    
    data = imd.open_data(var_type, year, year, file_format, input_folder)
    transform = params[var_type]['affine']
    
    # Transport array and flip the rows upside down
    output = data.data.transpose(0, 2 ,1)[:, ::-1, :]
    if calendar.isleap(year):
        count = 366
    else:
        count = 365
    
    if not output_filepath.parent.exists():
        output_filepath.parent.mkdir()
    
    dataset = rasterio.open(output_filepath, 'w', 
                                driver='GTiff',
                                height=params[var_type]['height'],
                                width=params[var_type]['width'],
                                count=count,
                                nodata=None,
                                dtype=np.float64,
                                crs='+proj=latlong',
                                transform=transform)
    dataset.write(output)
    dataset.close()

def main():
    """
    converts GRD to Tif ('rain','tmax' or 'tmin') and puts each in their respective sub-folders
    
    Args:
        var_type:str, either 'rain','tmax' or 'tmin'
        start_yr:int, for rain, between 1901 and 2020, for tmax/tmin, between 1951 and 2020
        end_yr:int, for rain, between 1901 and 2020, for tmax/tmin, between 1951 and 2020
    
    Example:
    python Code/atree/scripts/rainfall/IMDHistoricalGrid2Tif.py rain 2018 2019
    
    Output:
    {Home Dir}/Data/imd (respective folders for grd and tif)
    """
    var_type = sys.argv[1]        #('rain','tmax' or 'tmin') 
    start_yr = int(sys.argv[2])  #must be yyyy
    end_yr = int(sys.argv[3])    #must be yyyy
#     print(var_type,start_yr,end_yr,dataFol)
    
    for year in range(start_yr, end_yr+1):
        if var_type=="rain":
            input_file = '{}.grd'.format(year)
        else:
            input_file = '{}.GRD'.format(year)
        output_file = '{}.tif'.format(year)
    
        input_filepath = dataFol.joinpath(var_type, input_file)
        grd_filepath = dataFol.joinpath(var_type, 'grd', input_file)
        tif_filepath = dataFol.joinpath(var_type, 'tif', output_file)
#         print(input_filepath,grd_filepath,tif_filepath)
        
        read_convert_write(year, str(dataFol), var_type, tif_filepath)    # Path must be str because imdlib needs str
        # move grd data into respective grd directory
        if tif_filepath.exists():
            print(input_file + " > " + output_file + " successful")
            if not grd_filepath.parent.exists():
                grd_filepath.parent.mkdir()
            input_filepath.replace(grd_filepath)
            if grd_filepath.exists():
                print(input_file,": copy to grd folder successful")
            else:
                print(input_file,": copy to grd folder failed")
        else:
            print(input_file + " > " + output_file + " failed")

if __name__=='__main__':
    main()