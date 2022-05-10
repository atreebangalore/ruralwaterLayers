"""
Download of Gridded data for Precipitation or Max Temp or Min Temp
provided by the Indian Meteorological Department (IMD) 
"""
import sys
from pathlib import Path
import imdlib as imd

dataFol = Path.home().joinpath('Data','imd')
dataFol.mkdir(parents=True, exist_ok=True)

def main():
    """
    Downloads 'rain','tmax' or 'tmin' to the Data Folder in Home Directory
    
    Args:
        var_type:str, either 'rain','tmax' or 'tmin'
        start_yr:int, for rain, between 1901 and 2020, for tmax/tmin, between 1951 and 2020
        end_yr:int, for rain, between 1901 and 2020, for tmax/tmin, between 1951 and 2020
    
    Example:
    python Code/atree/scripts/rainfall/IMDHistoricalGrid.py rain 2018 2019
    
    Output:
    Gridded data stored in {Home Dir}/Data/imd
    """
    var_type = sys.argv[1]
    start_yr = int(sys.argv[2])
    end_yr = int(sys.argv[3])
    # print(var_type,start_yr,end_yr,dataFol)
    
    data = imd.get_data(var_type, start_yr, end_yr, fn_format='yearwise',file_dir=str(dataFol))  # Path must be str because imdlib needs str
    
if __name__=='__main__':
    main()