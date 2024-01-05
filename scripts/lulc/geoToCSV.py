import os
import numpy as np
import pandas as pd
import rasterio

path = r"C:\Users\atree\Documents\WELL_Labs\jaltol\Data\Prarambha-Distributaries"
LULC_path = os.path.join(path, "LULC_Canal_Rasters")
excel_path = os.path.join(path, 'excel_map.xlsx')

for tif in os.listdir(LULC_path):
    if os.path.splitext(tif)[1] == '.tif':
        print(tif)
        filepath = os.path.join(LULC_path, tif)
        filename = os.path.splitext(tif)[0]
        with rasterio.open(filepath) as src:
            band = src.read(1)
        df = pd.DataFrame(band)
        excel_mode = 'a' if os.path.exists(excel_path) else 'w'
        with pd.ExcelWriter(excel_path, mode=excel_mode, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=filename, index=False, header=False)

print(excel_path)

df = pd.ExcelFile(excel_path)
print(df.sheet_names)

# # Open the GeoTIFF file
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
