import os,sys
from pathlib import Path
from subprocess import check_output
import platform

dataFol = Path.home().joinpath("Data","et","sebop")
dataFol.mkdir(parents=True,exist_ok=True)

if platform.system()=='Windows':
    wget_path = "C:\Windows\System32\wget.exe"
elif platform.system() == 'Linux':
    wget_path = ""  #change this path to wget location for Linux
elif platform.system() == 'Darwin':
    wget_path = ""  #change this path to wget location for Darwin

    
def main():
    """downloads monthly SEBOP ET images from USGS website
    """
    
    year = sys.argv[1]
    month = sys.argv[2]
    
    monthly_url = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/eta/downloads/"
    filename = "m" + str(year) + str(month) + ".zip"    # "m200306.zip"
    print(filename)
    dir_prefix = "-P " + "\"" + str(dataFol) + "\""
    print(dir_prefix)
    wget_comm = wget_path + " " + dir_prefix + " " + monthly_url + filename
    print(wget_comm)
    
    output = check_output(wget_comm)
    print(output)

if __name__=="__main__":
    main()