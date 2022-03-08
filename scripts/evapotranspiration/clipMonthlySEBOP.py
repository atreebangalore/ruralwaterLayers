"""
The SEBOP ET Global image clipped for the National Boundary extent.
soi_national_boundary.shp at {Home Dir}/Data/gis is required.
The output SEBOP ET image of getMonthlySEBOP for 
specified month and year located at {Home Dir}/Data/et/sebop/
in zip format will be the input for this script.
"""
import os,sys
from pathlib import Path
from subprocess import check_output
from zipfile import ZipFile

import fiona
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import numpy as np

dataFol = Path.home().joinpath("Data","et","sebop")
dataFol.mkdir(parents=True)

soi_boundary = Path.home().joinpath("Data","gis","soi_national_boundary.shp")


def main():
    """SEBOP ET image located at {Home Dir}/Data/et/sebop/
    for the specified month and year clipped for 
    soi_national_boundary.shp extent, Year and month should
    be same as getMonthlySEBOP.py arguments.
    
    Args:
        year (YYYY): year for the monthly SEBOP ET images to be fetched.
        month (MM): specific month for the SEBOP ET image to be downloaded.
    
    Example:
    python Code/atree/scripts/evapotranspiration/clipMonthlySEBOP.py 2019 06
    
    Output:
    extracted global image and clipped tif image in {Home Dir}/Data/et/sebop/
    """
    
    year = sys.argv[1]
    month = sys.argv[2]
    
    # opening the zip file
    zipname = "m" + str(year) + str(month) + ".zip"
    print("name of zip file: ",zipname)
    
    zippath = str(dataFol) + "\\" + zipname
    print("path of zip file: ",zippath)
    
    with ZipFile(zippath, 'r') as zip:
        # printing all the contents of the zip file
        tifname = [name for name in zip.namelist() if name.endswith('.tif')][0]
        tifpath = str(dataFol) + "\\" + tifname
        print("path of tif file: ",tifpath)

        # extracting all the files
        print('Extracting all the files now...')
        zip.extractall(path=str(dataFol))
        print('Done!')
    
    # opening the geom to clip
    with fiona.open(str(soi_boundary), "r") as shapefile:
        shapes = [feature["geometry"] for feature in shapefile]
        print("india boundary imported for clip")
    
    # using rasterio to open and mask image
    with rasterio.open(str(tifpath)) as src:
        out_image, out_transform = mask(src, shapes, crop=True)
        out_meta = src.meta
        print("SEBOP image clipped")
    
    out_meta.update({"driver": "GTiff",
                "height": out_image.shape[1],
                "width": out_image.shape[2],
                "transform": out_transform})
    
    india_tifpath = Path(tifpath).parent.joinpath(Path(tifpath).stem + "_india" + Path(tifpath).suffix)
    
    with rasterio.open(india_tifpath, "w", **out_meta) as dest:
        dest.write(out_image)
        print("SEBOP image written to file: ",india_tifpath)
    
if __name__=="__main__":
    main()