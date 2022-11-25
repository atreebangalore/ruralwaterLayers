"""get area of different classes from Ganesh's LULC layer.
"""
import sys
from pathlib2 import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import ee
ee.Initialize()

classes = ('Western Ghats, Elevated Forest, Plantation',
'Unirrigated Plantation',
'Urban',
'Irrigated Horticulture, Plantation',
'Annually copped Paddy',
'Kharif-Rabi cropped Paddy',
'Rabi-Zaid cropped Paddy',
'Kharif-Zaid cropped Paddy',
'Kharif cropped Paddy',
'Rabi cropped Paddy',
'Zaid cropped Paddy',
'Kharif-Rabi Mix Crop',
'Rabi-Zaid Mix Crop',
'Kharif-Zaid Mix Crop',
'Kharif Mix Crop',
'Rabi Mix Crop',
'Zaid Mix Crop',
'Perennial Water Bodies',
'Seasonal Water Bodies',
'Annually Fallow, Open, Barren',
'Permanent Fallow land')


def get_lulc_image(year):
    return ee.Image(f"users/cseicomms/lulc_13class/KA_{year}")

def get_area_image(image):
    return ee.Image.pixelArea().divide(1e4).addBands(image)

def get_state_geometry(state):
    dist_map = ee.FeatureCollection('users/jaltol/FeatureCol/District_Map_2011')
    return dist_map.filter(ee.Filter.eq('ST_NM',state))#.geometry()

def calc_area(feature, area_image):
    params = {
    'reducer': ee.Reducer.sum().group(1, 'group'), 
    'geometry': feature.geometry(), 
    'scale': 30,
    'maxPixels': 1e12,
    }
    return area_image.reduceRegion(**params).getInfo()

def calc_info(feature, area_image):
    dist_name = feature.getInfo()['properties']['DISTRICT']
    area_classified = calc_area(feature, area_image)
    return dist_name, area_classified

def main(year, state, out_path):
    lulc = get_lulc_image(year)
    area_image = get_area_image(lulc)
    state_fc = get_state_geometry(state)
    fc_size = state_fc.size().getInfo()
    fc_list = state_fc.toList(fc_size)
    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = [ex.submit(calc_info, ee.Feature(fc_list.get(num)), area_image) for num in range(fc_size)]
    final = [future.result() for future in as_completed(futures)]
    out_dict = {}
    for f in final:
        dist_name, area_dict = f
        out_dict[dist_name] = {}
        area_list = area_dict['groups']
        for group in area_list:
            out_dict[dist_name][classes[group['group']]] = group['sum']
    df = pd.DataFrame(out_dict).T
    df.to_csv(out_path.joinpath(f'{state}-{year}.csv'))

if __name__ == '__main__':
    year = int(sys.argv[1])
    state = sys.argv[2]
    out_path = Path.home().joinpath('Code', 'atree', 'data', 'lulc')
    main(year, state, out_path)