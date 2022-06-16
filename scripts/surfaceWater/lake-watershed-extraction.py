"""

"""

import os,sys
from pathlib import Path
import ee
ee.Initialize()

root = Path.home() # find project root
config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]

opPath = root.joinpath("Code","atree","outputs","surfaceWater")
opPath.mkdir(parents=True,exist_ok=True) # create if not exist

s2coll = ee.ImageCollection("COPERNICUS/S2_SR")
hydrosheds_l12 = ee.FeatureCollection("WWF/HydroSHEDS/v1/Basins/hybas_12")
dem15s = ee.Image("WWF/HydroSHEDS/15CONDEM")
# geometry = ee.Geometry.Point([77.61373310755093, 13.062361380809758]);

def main():
    """
    Args:

    Example:
    python atree/scripts/surfacewater/lake-watershed-extraction.py 2021 12 1000 13.06236 77.61373

    Output:

    """

    yr = int(sys.argv[1])  # 2018 or later  # 2021
    month = int(sys.argv[2])  # don't use monsoon months (6,7,8,9)  # 12
    radius = int(sys.argv[3])    
    latitude = float(sys.argv[4]) # requires 4 decimal places 13.06236
    longitude = float(sys.argv[5])  # 77.61373
    geometry = ee.Geometry.Point([longitude,latitude]) 
    print(yr,month,radius,latitude,longitude)

    image = s2coll.filterBounds(geometry).filter(
        ee.Filter.And(
            ee.Filter.calendarRange(yr,yr,'year'),
            ee.Filter.calendarRange(month,month,'month')
            )
            ).min()
    # print(image.getInfo())

    def setArea(f):
        a = f.area(1)
        return(f.set('area',a))

    ndwi = image.normalizedDifference(['B3','B8'])      # METHOD 1 # good for water bodies
    wb = ndwi.gt(0.14).selfMask()
    wbv = wb.reduceToVectors(
    geometry=ee.Geometry(geometry.buffer(radius)), 
    scale= ee.Number(10)
    ).map(setArea)

    maxArea = wbv.reduceColumns(ee.Reducer.max(),['area']).get("max")
    biggestPolygon = wbv.filter(ee.Filter.eq('area',maxArea)).first()
    coords = biggestPolygon.getInfo()['geometry']['coordinates'][0]
    print(maxArea.getInfo())

    # make geojson of coords


    # identify hydrosheds boundary in gee
    hydroshed = hydrosheds_l12.filterBounds(geometry)
    print(type(hydroshed))

    # clip hydroshed tif
    hydroshed_dem = dem15s.clip(hydroshed)
    scale = hydroshed_dem.projection().nominalScale()
    print(scale.getInfo())

    # get elevation at geometry with reduce region

    # mask DEM using elevation at geometry
    hydroshed_dem_above_lake = hydroshed_dem.updateMask(hydroshed_dem.gte(886))
    
    # export DEM
    # def downloadImg:
    downloadArgs = {'name':'dem_clip','region':hydroshed.first().geometry(),'format':"GEO_TIFF",'scale':scale}
    res = hydroshed_dem_above_lake.getDownloadURL(downloadArgs)
    print(type(res))
    print(res)

    # saga toolbox


    # calculate watershed




if __name__=='__main__':
    main()

