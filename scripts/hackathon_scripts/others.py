import ee
ee.Initialize()
from datetime import datetime
import pandas as pd
from pathlib import Path
from itertools import product

district_name = 'raichur'
village_name = 'sanbal'

district_fc = ee.FeatureCollection(
    'users/jaltolwelllabs/hackathonDists/hackathon_dists'
    ).filter(ee.Filter.eq('district_n', district_name))
village_fc = district_fc.filter(ee.Filter.eq('village_na', village_name))
village_geometry = village_fc.geometry()
precipitation_collection = ee.ImageCollection("users/jaltolwelllabs/IMD/rain")

dataFol = Path.home().joinpath("Data", "hackathon", village_name)
dataFol.mkdir(parents=True, exist_ok=True)

print('started!!!')

fabdem = ee.ImageCollection("projects/sat-io/open-datasets/FABDEM").mosaic()
srtm = ee.Image('USGS/SRTMGL1_003').select('elevation')
srtm_slope = ee.Terrain.slope(srtm)
org_carbon = ee.Image("OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02").multiply(5)
clay = ee.Image("OpenLandMap/SOL/SOL_CLAY-WFRACTION_USDA-3A1A1A_M/v02")
bulk_density = ee.Image("OpenLandMap/SOL/SOL_BULKDENS-FINEEARTH_USDA-4A1H_M/v02").multiply(10)

datasets = [
    ('elevation(m)', fabdem, 'b1'),
    ('slope(deg)', srtm_slope, 'slope'),
    ('Soil Org Carbon(g/kg)(0cm)', org_carbon.select(['b0']), 'b0'),
    ('Soil Org Carbon(g/kg)(10cm)', org_carbon.select(['b10']), 'b10'),
    ('Soil Org Carbon(g/kg)(30cm)', org_carbon.select(['b30']), 'b30'),
    ('Soil Org Carbon(g/kg)(60cm)', org_carbon.select(['b60']), 'b60'),
    ('Soil Org Carbon(g/kg)(100cm)', org_carbon.select(['b100']), 'b100'),
    ('Soil Org Carbon(g/kg)(200cm)', org_carbon.select(['b200']), 'b200'),
    ('Clay Content(%)(0cm)', clay.select(['b0']), 'b0'),
    ('Clay Content(%)(10cm)', clay.select(['b10']), 'b10'),
    ('Clay Content(%)(30cm)', clay.select(['b30']), 'b30'),
    ('Clay Content(%)(60cm)', clay.select(['b60']), 'b60'),
    ('Clay Content(%)(100cm)', clay.select(['b100']), 'b100'),
    ('Clay Content(%)(200cm)', clay.select(['b200']), 'b200'),
    ('Soil Bulk Density(kg/m3)(0cm)', bulk_density.select(['b0']), 'b0'),
    ('Soil Bulk Density(kg/m3)(10cm)', bulk_density.select(['b10']), 'b10'),
    ('Soil Bulk Density(kg/m3)(30cm)', bulk_density.select(['b30']), 'b30'),
    ('Soil Bulk Density(kg/m3)(60cm)', bulk_density.select(['b60']), 'b60'),
    ('Soil Bulk Density(kg/m3)(100cm)', bulk_density.select(['b100']), 'b100'),
    ('Soil Bulk Density(kg/m3)(200cm)', bulk_density.select(['b200']), 'b200'),
]

def getStats(image: ee.Image, geometry: ee.Geometry, reducer, band_name) -> ee.Image:
    if reducer == 'min':
        red = ee.Reducer.min()
    elif reducer == 'max':
        red = ee.Reducer.max()
    elif reducer == 'median':
        red = ee.Reducer.median()
    else:
        red = ee.Reducer.mean()
    stats = image.reduceRegion(
        reducer=red,
        geometry=geometry,
        scale=30
    )
    return stats.getInfo()[band_name]

out_dict = {}
for data in datasets:
    label, image, band_name = data
    for reducer in ('max', 'mean', 'median', 'min'):
        out_dict.setdefault(label, {}).update({reducer:getStats(image, village_geometry, reducer, band_name)})

df = pd.DataFrame(out_dict).T
filepath = dataFol.joinpath('terrain_soilProps.csv')
df.to_csv(filepath)
print(f'completed: {filepath}')

texture = ee.Image("OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02")
tex_classes = ['Cl', 'SiCl', 'SaCl', 'ClLo', 'SiClLo', 'SaClLo', 'Lo', 'SiLo', 'SaLo', 'Si', 'LoSa', 'Sa']
tex_dict = {}
for depth in ('0', '10', '30', '60', '100', '200'):
    tex_image = texture.select([f'b{depth}'])
    tex_dict[f'{depth}cm depth'] = {}
    for ix, name in enumerate(tex_classes, start=1):
        class_image = tex_image.eq(ix)
        area_image = class_image.multiply(ee.Image.pixelArea())
        stats = area_image.reduceRegion(
            reducer=ee.Reducer.sum(),
            geometry=village_geometry,
            scale=30
        ).getInfo()[f'b{depth}']
        tex_dict[f'{depth}cm depth'][f'{name} (m2)'] = stats

df = pd.DataFrame(tex_dict)
tex_file = dataFol.joinpath('soil_Texture.csv')
df.to_csv(tex_file)
print(f'completed: {tex_file}')
