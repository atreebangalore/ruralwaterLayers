"""
Extract the ET SEBOP raster pixel values of every
district in the chosen state for the water year of imagery.
"""
# https://gis.stackexchange.com/questions/260304/extract-raster-values-within-shapefile-with-pygeoprocessing-or-gdal
import sys
from pathlib import Path
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import numpy as np

root = Path(__file__).parent.parent.parent.parent.absolute() # find project root
data = root.joinpath("data","evapotranspiration","SEBOP","yearly")
boundaries = Path.home().joinpath("Data","gis")
# sys.path.append(str(root))    # this allows lib and config modules below to be found


def clipValues(geom,tifPath,district,year):
    """Extraction of ET SEBOP Pixel Values.
    requires individual shape files for the states
    to be located at {Home Dir}/Data/gis

    Args:
        geom (geojson): geometry of the district
        tifPath (string): Path of ET SEBOP raster
        district (string): name of the district
        year (integer): argument provided to the script
    """
    # extract the raster values values within the polygon 
    with rasterio.open(tifPath) as src:
        out_image, out_transform = mask(src, geom, crop=True)
#     print(out_image.shape)
    
    # no data values of the original raster
    no_data=src.nodata
#     print(no_data)
    
    # extract the values of the masked array
    etdata = out_image[0]
    
    values = etdata[np.where(etdata!=no_data)]
    print("median: ", np.median(values),"\n",
        "range: ", np.max(values)-np.min(values))
    statsPath = data.joinpath("stats")
    statsPath.mkdir(parents=True,exist_ok=True) # create if not exist
    statsPath = statsPath.joinpath(district + "_" + year + ".csv")
#     print(statsPath)
    values.tofile(statsPath, sep = ',')
    
def main():
    """Extraction of ET pixel values of all districts
    in the chosen state
    
    Args:
    state name (string): state name as in {state}_district_boundary.shp
    year: year for which getWaterYrSEBOP.py was executed
    
    Example:
    python Code/atree/scripts/evapotranspiration/getDistrictValues.py tamilnadu 2019
    
    Output:
    individual csv files for all districts in the path
    Code/data/evapotranspiration/SEBOP/yearly/stats
    """
    state = sys.argv[1]
    year = sys.argv[2]
    
    stateBPath = boundaries.joinpath(state+"_district_boundaries.shp")
    tifPath = data.joinpath("y"+year+"_modisSSEBopETv4_actual_mm.tif")
    print(tifPath,tifPath.exists())
    
    stategdf = gpd.read_file(str(stateBPath))
    districts = stategdf.DISTRICT
    
    geoms = stategdf.geometry.values  # list of shapely geometries
#     print(type(geoms[0]))  # <class 'shapely.geometry.polygon.Polygon'>
    
    # transform to GeoJSON format
    from shapely.geometry import mapping
        
    for district,geom in zip(districts,geoms):
        district = district.replace(" ","")
        print(district)
        geom = [mapping(geom)] # from shapely.geometry to [geojson]
        clipValues(geom,tifPath,state,district,year)
    
if __name__=="__main__":
    main()