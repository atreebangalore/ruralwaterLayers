"""download near real time IMD daily data including precipitation,
minimum and maximum temperature
"""
import sys, os
from pathlib import Path
from imddaily import imddaily
from datetime import datetime

def main(var_type, start_date, end_date, grd_path, tif_path):
    """download NRT IMD Data

    Usage:
    python Code/atree/scripts/rainfall/IMD_NRT.py [var_type] [start_date] [end_date]

    Args:
        var_type (str): "rain" or "tmax" or "tmin" or "raingpm" or "tmaxone" or "tminone"
        start_date (str): start date in YYYY-MM-DD
        end_date (str): end date in YYYY-MM-DD
    
    Example:
    python Code/atree/scripts/rainfall/IMD_NRT.py rain 2020-01-01 2020-12-31

    Output:
    {Home Dir}/Data/imd/NRT
    """
    now = datetime.now().strftime('%Y%m%d%H%M%S')
    today_grd = grd_path.joinpath(var_type, now)
    today_tif = tif_path.joinpath(var_type, now)
    today_grd.mkdir(parents=True, exist_ok=True)
    today_tif.mkdir(parents=True, exist_ok=True)
    data = imddaily.get_data(var_type, start_date, end_date, today_grd)
    data.to_geotiff(today_tif)
    suffix = {
        "raingpm": "raingpm_",
        "tmax": "tmax_",
        "tmin": "tmin_",
        "rain": "rain_",
        "tmaxone": "tmax1_",
        "tminone": "tmin1_",
    }
    for file in os.listdir(today_tif):
        old_path = os.path.join(today_tif, file)
        new = file.replace(suffix[var_type],'')
        new_path = os.path.join(today_tif, new)
        os.rename(old_path, new_path)

if __name__=='__main__':
    var_type = sys.argv[1]
    start_date = sys.argv[2]
    end_date = sys.argv[3]
    grd_path = Path.home().joinpath('Data','imd','NRT','grd')
    tif_path = Path.home().joinpath('Data','imd','NRT','tif')
    grd_path.mkdir(parents=True, exist_ok=True)
    tif_path.mkdir(parents=True, exist_ok=True)
    main(var_type, start_date, end_date, grd_path,tif_path)