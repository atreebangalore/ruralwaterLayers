import os,sys
from pathlib import Path
from subprocess import check_output

dataFol = Path.home().joinpath("Data","et","sebop")

def main():
    """downloads monthly SEBOP ET images from USGS website
    """
    
    year = sys.argv[1]
    month = sys.argv[2]
    
    monthly_url = "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/eta/downloads/"
    filename = "m" + str(year) + str(month) + ".zip"
    print(filename)
    dir_prefix = "-P " + "\"" + str(dataFol) + "\""
    print(dir_prefix)
    wget_comm = "C:\Windows\System32\wget.exe" + " " + dir_prefix + " " + monthly_url + filename
    print(wget_comm)
    
    output = check_output(wget_comm)
    print(output)

if __name__=="__main__":
    main()