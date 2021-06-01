import sys
import os
from pathlib import Path
import imdlib as imd

dataFol = Path.home().joinpath('Data','imd')  

def main():
    """
    Downloads 'rain','tmax' or 'tmin' to the Data Folder in Home Directory
    
    Args:
        var_type:str, either 'rain','tmax' or 'tmin'
        start_yr:int, for rain, between 1901 and 2020, for tmax/tmin, between 1951 and 2020
        end_yr:int, for rain, between 1901 and 2020, for tmax/tmin, between 1951 and 2020
    """
    var_type = sys.argv[1]
    start_yr = int(sys.argv[2])
    end_yr = int(sys.argv[3])
    print(var_type,start_yr,end_yr,dataFol)
    
    data = imd.get_data(var_type, start_yr, end_yr, fn_format='yearwise',file_dir=str(dataFol))  # Path must be str because imdlib needs str
    
if __name__=='__main__':
    main()