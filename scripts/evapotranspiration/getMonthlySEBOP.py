"""
Download of SEBOP ET images from the USGS portal
for the given year and month provided as arguments.
This script requires wget to be installed.
"""
import sys
from pathlib import Path
from subprocess import check_output
import platform

dataFol = Path.home().joinpath("Data","et","sebop")
dataFol.mkdir(parents=True,exist_ok=True)

if platform.system()=='Windows':
    wget_path = "C:\Windows\System32\wget.exe"
elif platform.system() == 'Linux':
    wget_path = "/usr/bin/wget"  #change this path to wget location for Linux
elif platform.system() == 'Darwin':
    wget_path = "/usr/local/bin/wget"  #change this path to wget location for Darwin

    
def main():
    """Downloads SEBOP ET images,
    by generating corresponding wget command.
    
    Args:
        year (YYYY): year for the monthly SEBOP ET images to be fetched.
        month (MM): specific month for the SEBOP ET image to be downloaded.
    
    Example:
    python Code/atree/scripts/evapotranspiration/getMonthlySEBOP.py 2019 06
    
    Output:
    zip file will be stored in {Home Dir}/Data/et/sebop/
    """
    
    year = sys.argv[1]
    month = sys.argv[2]
    
    monthly_url = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/eta/downloads/"
    filename = "m" + str(year) + str(month) + ".zip"    # "m200306.zip"
    print(filename)
    exists = dataFol.joinpath(filename).exists()
    print(exists)

    if not exists:
        print("file does not exist, hence downloading...")
        dir_prefix = "-P " + "\"" + str(dataFol) + "\""
        print(dir_prefix)
        wget_comm = wget_path + " " + dir_prefix + " " + monthly_url + filename
        print(wget_comm)
    
        output = check_output(wget_comm,shell=True)
        print(output)

if __name__=="__main__":
    main()