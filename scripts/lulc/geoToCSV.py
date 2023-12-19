import rasterio
import numpy as np
import pandas as pd

# Open the GeoTIFF file
with rasterio.open("C:\\Users\\ATREE\\Documents\\CSEI-ATREE\\Raichur\\Distributary10_LULC_2021_22.tif") as src:
    # Read a specific band (e.g., band 1)
    band = src.read(1)

# Convert the band to a 1D array
# flattened_band = band.flatten()

# Create a DataFrame
df = pd.DataFrame(band)

# Export to CSV
df.to_csv('C:\\Users\\ATREE\\Documents\\CSEI-ATREE\\Raichur\\Distributary10_LULC_2021_22.csv', index=True, header=True)
df.to_csv('C:\\Users\\ATREE\\Documents\\CSEI-ATREE\\Raichur\\Distributary10_LULC_2021_22_noindex.csv', index=False)
