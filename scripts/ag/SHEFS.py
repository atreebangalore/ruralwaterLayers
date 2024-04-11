import ee
ee.Initialize()
import pandas as pd
import os

dir_path = r'C:\Users\atree\Data\ag\SHEFS'

points = ee.FeatureCollection('users/balakumaranrm/SHEFS_Plot_Locations')

OLM_bands = ['b0', 'b10', 'b30', 'b60', 'b100', 'b200']
whrc_bands = ['Mg']
ornl_bands = ['agb', 'bgb']
isda_bands = ['mean_0_20', 'mean_20_50']

openLandMap = ee.Image("OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02").select(OLM_bands)
whrc = ee.Image("WHRC/biomass/tropical").select(whrc_bands)
ornl = ee.ImageCollection("NASA/ORNL/biomass_carbon_density/v1").select(ornl_bands).mosaic()
isda = ee.Image("ISDASOIL/Africa/v1/carbon_organic").select(isda_bands)

def get_data(image, points):
    return image.sampleRegions(
    collection=points,
    scale=image.projection().nominalScale(),
    ).getInfo()

def extract_data(value_dict, band_list):
    out_dict = {}
    for ix, feature in enumerate(value_dict['features']):
        info = feature['properties']
        out_dict[ix] = {
            'Lat': info['Latitude'],
            'Long': info['Longitude'],
        }
        for band in band_list:
            out_dict[ix].update({band:info[band]})
    return pd.DataFrame(out_dict).T

def save_csv(df, path):
    df.to_csv(path, index=False)

# OLM_values = get_data(openLandMap, points)
# whrc_values = get_data(whrc, points)
# ornl_values = get_data(ornl, points)
# isda_values = get_data(isda, points)

OLM_path = os.path.join(dir_path, 'OpenLandMap.csv')
whrc_path = os.path.join(dir_path, 'WHRC.csv')
ornl_path = os.path.join(dir_path, 'ORNL.csv')
isda_path = os.path.join(dir_path, 'iSDAsoil.csv')

data_list = (
    (get_data(openLandMap, points), OLM_bands, OLM_path),
    (get_data(whrc, points), whrc_bands, whrc_path),
    (get_data(ornl, points), ornl_bands, ornl_path),
    (get_data(isda, points), isda_bands, isda_path)
)

for value, band, path in data_list:
    print(f'working on {path}')
    save_csv(extract_data(value, band), path)

print('completed!!!')
