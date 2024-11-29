import os
import numpy as np
import pandas as pd
import rasterio
import os
from qgis import processing
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsRasterLayer, QgsDistanceArea, QgsCoordinateReferenceSystem, QgsField, QgsFeature, QgsPointXY, QgsGeometry, QgsProcessingUtils, QgsProcessingContext, QgsExpression

# STEP 1 - clip LULC images
"""
Inputs:
1. Rectangular shapefile covering AOI
2. Download the LULC images for different years

Command:
gdalwarp -overwrite -s_srs EPSG:4326 -t_srs EPSG:4326 -of GTiff -cutline \
C:/Users/atree/Documents/WELL_Labs/jaltol/Data/Prarambha-Distributaries/Excel_Tool/D10_shapefiles/D10-extent.shp \
-cl D10-extent -crop_to_cutline \
C:/Users/atree/Documents/WELL_Labs/jaltol/Data/IITD-LULC/Raichur/Raichur_LULC_Version2/KARNATAKA_RAICHUR_2022-07-01_2023-06-30_LULCmap_10m.tif \
C:/Users/atree/Documents/WELL_Labs/jaltol/Data/Prarambha-Distributaries/Excel_Tool/lulc_rasters/2022-2023_clipped.tif
"""
root_folder = r'C:/Users/atree/Documents/WELL_Labs/jaltol/Data/Prarambha-Distributaries/Excel_Tool'
extent_shp = os.path.join(root_folder, 'D10_shapefiles','D10-extent.shp')
raw_lulc_folder = r'C:/Users/atree/Documents/WELL_Labs/jaltol/Data/IITD-LULC/Raichur/Raichur_LULC_Version2'
clip_folder = os.path.join(root_folder, 'lulc_rasters')
lulc_px_shp = os.path.join(root_folder, 'D10_shapefiles','D10_LULC_Pixels.shp')
gen_raster_folder = os.path.join(root_folder, 'generated_rasters')
correct_folder = os.path.join(root_folder, 'corrected_rasters')
final_folder = os.path.join(root_folder, 'final_rasters')
excel_path = os.path.join(root_folder, 'excel_map_selected_FIC.xlsx')
def file2yr(filename):
    return filename.replace('KARNATAKA_RAICHUR_','').replace('-07-01','').replace('-06-30_LULCmap_10m','')

for file in os.listdir(raw_lulc_folder):
    if not file.endswith('.tif'):
        continue
    lulc_image = os.path.join(raw_lulc_folder, file)
    if os.path.exists(lulc_image):
        print(f'skipped clipping {file}')
        continue
    clipped_image = os.path.join(clip_folder, file)
    params = {
        'INPUT':lulc_image,
        'MASK':extent_shp,
        'SOURCE_CRS':QgsCoordinateReferenceSystem('EPSG:4326'),
        'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:4326'), #None,
        'TARGET_EXTENT':None,
        'NODATA':None,
        'ALPHA_BAND':False,
        'CROP_TO_CUTLINE':True,
        'KEEP_RESOLUTION':False,
        'SET_RESOLUTION':False,
        'X_RESOLUTION':None,
        'Y_RESOLUTION':None,
        'MULTITHREADING':False,
        'OPTIONS':'',
        'DATA_TYPE':0,
        'EXTRA':'',
        'OUTPUT':clipped_image
    }
    result = processing.run("gdal:cliprasterbymasklayer", params)
    print(f'{file} clipped!')

# Step 2 - create skeleton shp
"""
1. Load one LULC image in QGIS
2. execute processing tool "Rater Pixels to Polygons"
once the polygon layer is generated, go to attribute table
Field Calculator -> update existing field -> select "VALUE" field
under expression text box write 0
click ok and save the edits
"""
if os.path.exists(lulc_px_shp):
    print(f'{lulc_px_shp} already exists')
else:
    sample_image = os.listdir(clip_folder)[0]
    params = {
        'INPUT_RASTER':sample_image,
        'RASTER_BAND':1,
        'FIELD_NAME':'VALUE',
        'OUTPUT':'TEMPORARY_OUTPUT'
    }
    result = processing.run("native:pixelstopolygons", params)
    print(f'generated {lulc_px_shp}')

# step 3 - generate different rasters
"""
1. create a copy of the lulc_px_shp (skeleton shp) and open it
2. open the water network shp
3. run select by location and select polygons overlaying the water network
4. open field calculator
5. check only update x selected features
6. check update exisiting field and select VALUE
7. under expression text box write 100 for water network
8. click ok and save the edits
9. Raster -> Conversion -> Rasterize
Input layer
Field
output raster size units = Georeferenced uints
Width/Horizontal resolution = 0.00009
Height/Vertical resoulution = 0.00009
output data type = Int32
Output file location
Run
"""

# step 3 - alternative
"""
1. open the farm plots shp and add the corresponding pixel values in column "descriptio" make sure it is int type
2. open the "Join attributes by location" tool
Join to Features in : lulc_px_shp
untick intersect
tick "are within"
By comparing to: Farm boundary shp
Fields to add: descriptio
Join type: one to many
output file location: save as farm_pxs.shp
Run
3. Raster -> Conversion -> Rasterize
Input layer
Field
output raster size units = Georeferenced uints
Width/Horizontal resolution = 0.00009
Height/Vertical resoulution = 0.00009
output data type = Int32
Output file location
Run
"""

# step 4 - correct the images
for file in os.listdir(gen_raster_folder):
    if not file.endswith('.tif'):
        continue
    filepath = os.path.join(gen_raster_folder, file)
    outpath = os.path.join(correct_folder, file)
    if os.path.exists(outpath):
        print(f'skipped correcting {file}')
    else:
        params = {
            'map':filepath,
            'setnull':'','null':0,'-f':False,'-i':False,'-n':False,'-c':False,
            '-r':False,'output':outpath,'GRASS_REGION_PARAMETER':None,
            'GRASS_REGION_CELLSIZE_PARAMETER':0,'GRASS_RASTER_FORMAT_OPT':'',
            'GRASS_RASTER_FORMAT_META':''}
        result = processing.run("grass7:r.null", params)
        print(f'{file} corrected')

# step 5 - sum all the rasters (water, farm, lulc)
for file in os.listdir(clip_folder):
    if not file.endswith('.tif'):
        continue
    filepath = os.path.join(clip_folder, file)
    with rasterio.open(filepath, 'r') as f:
        profile = f.profile
        data = f.read(1)
    for c in os.listdir(correct_folder):
        if not c.endswith('.tif'):
            continue
        cpath = os.path.join(correct_folder, c)
        with rasterio.open(cpath, 'r') as z:
            cdata = z.read(1)
        data += cdata
    outpath = os.path.join(final_folder, file)
    if os.path.exists(outpath):
        print(f'skipped final {file}')
    else:
        with rasterio.open(outpath, 'w', **profile) as dst:
            dst.write(data, 1)
        print(f'{file} completed!!!')

if os.path.exists(excel_path):
        print(f'{excel_path} already exists')
else:
    for tif in os.listdir(final_folder):
        if os.path.splitext(tif)[1] == '.tif':
            print(tif)
            filepath = os.path.join(final_folder, tif)
            filename = os.path.splitext(tif)[0]
            with rasterio.open(filepath) as src:
                band = src.read(1)
            df = pd.DataFrame(band)
            excel_mode = 'a' if os.path.exists(excel_path) else 'w'
            with pd.ExcelWriter(excel_path, mode=excel_mode, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=file2yr(filename), index=False, header=False)
    print(f'{excel_path} completed!!!')

# df = pd.ExcelFile(excel_path)
# print(df.sheet_names)

# # Open the  Single GeoTIFF file
# with rasterio.open("C:\\Users\\ATREE\\Documents\\CSEI-ATREE\\Raichur\\Distributary10_LULC_2021_22.tif") as src:
#     # Read a specific band (e.g., band 1)
#     band = src.read(1)

# # Convert the band to a 1D array
# # flattened_band = band.flatten()

# # Create a DataFrame
# df = pd.DataFrame(band)

# # Export to CSV
# df.to_csv('C:\\Users\\ATREE\\Documents\\CSEI-ATREE\\Raichur\\Distributary10_LULC_2021_22.csv', index=True, header=True)
# df.to_csv('C:\\Users\\ATREE\\Documents\\CSEI-ATREE\\Raichur\\Distributary10_LULC_2021_22_noindex.csv', index=False)
