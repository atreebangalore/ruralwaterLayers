import os,sys
from pathlib import Path
from zipfile import ZipFile
import glob

from matplotlib import pyplot as plt
import numpy as np

import fiona
import rasterio
from rasterio.mask import mask
import geopandas as gpd

dataFol = Path.home().joinpath("Data","et","sebop")
dataFol.mkdir(parents=True, exist_ok=True)

# if not dataFol.exists():
#     Path.mkdir(dataFol)

soi_boundary = Path.home().joinpath("Data","gis","soi_national_boundary.shp")
# opening the geom to clip
with fiona.open(str(soi_boundary), "r") as shapefile:
    shapes = [feature["geometry"] for feature in shapefile]
    print("india boundary imported for clip")

def makeAnnualImage(matches,yr):
    # READ IN FILES TO BE SUMMED
    sum = None
    for file in matches:
        dataset = rasterio.open(file)
        month = dataset.read(1)
        out_meta = dataset.meta
        
        if sum is None:
            sum = month
        else:
            sum += month
    
    sum = np.where(sum==0,-32768,sum)
    #print(out_meta)
    
    sum_tifpath = dataFol.joinpath("wy" + yr + "_india.tif")
    
    # WRITING SUMMED ET TO FILE
    with rasterio.open(sum_tifpath, "w", **out_meta) as dest:
        dest.write(sum,1)
        print("SEBOP Water Year Cumulative Sum image written to file: ",sum_tifpath)

def clipImage(tifpath):
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

def unzipImage(zippath):    
    with ZipFile(zippath, 'r') as zip:
        # printing all the contents of the zip file
        tifname = [name for name in zip.namelist() if name.endswith('.tif')][0]
        tifpath = str(dataFol.joinpath(tifname))
        print("path of tif file: ",tifpath)
  
        # extracting all the files
        print('Extracting all the files now...')
        zip.extractall(path=str(dataFol))
        print('Done!')
        clipImage(tifpath)
        
def main():
    """calculates raster sum of monthly SEBOP ET images for water year, clips image and saves to file
    """
    
    yr = sys.argv[1]
    yr2 = str(int(yr) + 1)
    
    # GENERATE LIST OF (YEAR,MONTH) TUPLES
    monthseq = ['06','07','08','09','10','11','12','01','02','03','04','05']
    yearseq = [yr]*7 + [yr2]*5 
    monthyearseq = [*zip(yearseq,monthseq)]    # (2003,06), (2003,07), ..
    
    ###############    GET MONTHLY IMAGES    ################
    # PREPARE COMMAND
    getMonthly = "python getMonthlySEBOP.py {year} {month}"
    
    # CALL getMonthlySEBOP.py
    for year,month in monthyearseq:
        try:
            os.system(getMonthly.format(year=year,month=month))
        except:
            downloadStatus = "fail"
            sys.exit(f"monthly download failed, year:{year}, month:{month}")

    downloadStatus = "success"
    # print("download successful ")
   
    ###############    UNZIP & CLIP MONTHLY IMAGES  ################

    if downloadStatus == "success":
        for year,month in monthyearseq:
          # opening the zip file
            zipname = "m" + str(year) + str(month) + ".zip"
            print("name of zip file: ",zipname)
        
            zippath = str(dataFol.joinpath(zipname))
            print("path of zip file: ",zippath)
            unzipImage(zippath)
    
        ###############    PREP YEARLY IMAGE     ################
        # GENERATE LIST OF FILENAMES LIKE 'm200306*_india.tif','m200307*_india.tif',..
        monthlyfn = ['m' + year + month + "*_india.tif" for year,month in monthyearseq]
        print("monthly files to filter: ",monthlyfn,"\n")
    
        # FILTER FILES IN DATA FOLDER TO BE SUMMED
        os.chdir(str(dataFol))
        matches = []
        for pattern in monthlyfn:
            fn = glob.glob(pattern)
            matches += fn
            
        print("tifs to be summed: ",matches)
        makeAnnualImage(matches,yr)
    
if __name__=="__main__":
    main()