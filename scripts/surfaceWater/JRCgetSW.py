"""JRC Surface Water Images
Volume of Surface Water calculated using Power formula for both
PreMonsoon and PostMonsoon is Calculated and
exported from GEE to GDrive as tif
"""

from pathlib import Path
import ee
import sys
ee.Initialize()

root = Path.home() # find project root
config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]
opPath = root.joinpath("Code","atree","outputs","surfaceWater")
opPath.mkdir(parents=True,exist_ok=True) # create if not exist

import placenames

def main():
    """
    python Code/atree/scripts/surfaceWater/JRCgetSW.py [year] [ST]
    
    Arguments:
    Year (yyyy): Year for filtering the images.
    ST : Two letter abbreviated state name.
    
    Example:
    python Code/atree/scripts/surfaceWater/JRCgetSW.py 2019 KA
    
    Output:
    PreMonsoon and PostMonsoon Surface Water Volume tif images in GDrive
    """
    year = int(sys.argv[1])
    states = sys.argv[2].replace("[","").replace("]","").split(",")
    state_col = placenames.datameet_state_col_name
    
    chosen_states = [placenames.ST_names[state] for state in states]

    preDate = ee.Date.fromYMD(year,5,1) #2020-05-01
    postDate = [ee.Date.fromYMD(year+1,9,1),
                ee.Date.fromYMD(year+1,10,1),
                ee.Date.fromYMD(year+1,11,1)]
    boundaries = ee.FeatureCollection('users/cseicomms/boundaries/datameet_states_boundary')
    boundaries = boundaries.filter(ee.Filter.inList(state_col,chosen_states))

    iColl = ee.ImageCollection("JRC/GSW1_3/MonthlyHistory")
    PreMonsoon = (iColl.filterDate(preDate).mosaic()).remap([2],[1])\
        .clipToCollection(boundaries).reproject('EPSG:32643',None,30)
    PostMonsoon = ((iColl.filterDate(postDate[0]).mosaic()).remap([2],[1]))\
        .unmask(((iColl.filterDate(postDate[1]).mosaic()).remap([2],[1])),False)\
        .unmask(((iColl.filterDate(postDate[2]).mosaic()).remap([2],[1])),False)\
        .clipToCollection(boundaries).reproject('EPSG:32643',None,30);
    
    PreArea = PreMonsoon.multiply(ee.Image.pixelArea())
    PreVolume = ((PreArea.pow(ee.Image(1.5316)).multiply(0.0023)).rename('Volume'))
    PostArea = PostMonsoon.multiply(ee.Image.pixelArea())
    PostVolume = ((PostArea.pow(ee.Image(1.5316)).multiply(0.0023)).rename('Volume'))
    preTask = ee.batch.Export.image.toDrive(image=PreVolume,
                                    description='PreMonsoon Volume '+str(year),
                                    scale=30,
                                    region=boundaries.geometry(),
                                    fileNamePrefix='PreVolume'+str(year),
                                    crs='EPSG:32643',
                                    fileFormat='GeoTIFF',
                                    maxPixels=1e10)
    preTask.start()
    postTask = ee.batch.Export.image.toDrive(image=PostVolume,
                                    description='PostMonsoon Volume '+str(year),
                                    scale=30,
                                    region=boundaries.geometry(),
                                    fileNamePrefix='PostVolume'+str(year),
                                    crs='EPSG:32643',
                                    fileFormat='GeoTIFF',
                                    maxPixels=1e10)
    postTask.start()
    print('Completed! export to G-Drive started...')

if __name__=='__main__':
    main()