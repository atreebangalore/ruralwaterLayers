import sys
from pathlib import Path
import pandas as pd
import ee
ee.Initialize()

start_year = 2018
end_year = 2022
treatment = ee.FeatureCollection('users/balakumaranrm/PRADAN/villages_CH_WB')
control = ee.FeatureCollection('users/balakumaranrm/PRADAN/Control_Vill_CH_WB')
state_field = 'state_name'
district_field = 'district_n'
subdistrict_field = 'subdistric'
village_field = 'village_na'
unique_field = ('village_na', 'subdistric', 'district_n', 'state_name')

mod_path = str(Path.home().joinpath('Code','atree','scripts','WSI'))
sys.path.append(mod_path)
import indicators

print('Started!!!')

for title, roi in (('treatment',treatment), ('control',control)):
    access_out, kharif_out, rabi_out = {}, {}, {}
    for year in range(start_year, end_year+1):
        print(f'calculating for {title} {year}')
        access_scores, crop_area, irrig_area = indicators.access_indicator_IndiaSAT(year, roi, unique_field)
        access_out[year] = access_scores
        kharif_out[year] = crop_area
        rabi_out[year] = irrig_area
    access_path = Path(r'C:\Users\atree\Data\WSI').joinpath(f'{title}_access_indicator_IndiaSAT.csv')
    crop_path = Path(r'C:\Users\atree\Data\WSI').joinpath(f'{title}_crop_area_IndiaSAT.csv')
    irrig_path = Path(r'C:\Users\atree\Data\WSI').joinpath(f'{title}_irrig_area_IndiaSAT.csv')
    pd.DataFrame(access_out).to_csv(access_path)
    pd.DataFrame(kharif_out).to_csv(crop_path)
    pd.DataFrame(rabi_out).to_csv(irrig_path)
    print(f'completed {title}')

print('Completed!!!')