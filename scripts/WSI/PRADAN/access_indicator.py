import sys
from pathlib import Path
import pandas as pd
import ee
ee.Initialize()

start_year = 2018
end_year = 2023
shrug = ee.FeatureCollection('users/balakumaranrm/PRADAN/SHRUG_CH_WB')
unique_field = 'village_na'

similar_villages_path = r"C:\Users\atree\Data\slope\similar_villages_stdDev_slope.csv"
similar_villages = pd.read_csv(similar_villages_path)
# print(similar_villages.head())

Chattisgarh_villages = [
'sargawan',
'lodhi',
'murka',
'sarima',
'sihar',
'dimrapal',
'pathri',
'mailbeda',
'badedeoda',
'lawagaon',
'barejirakhal',
'mohera',
'chitaloor',
'kawalnar',
'ganjenar',
'masenar',
'hamirgarh',
'teknar',
'keratong',
'permaras',
'kindarwada',
'chipurpal',
'kapalphodi',
'bhandarwadi',
'birjhuli',
'khadma mal',
'boda',
'dholbajja',
'shambhu pipar',
'bahanakhodara',
'kahadgondi',
'markatola',
'golkumhada',
'tuaguhan',
'kasawahi',
'thanabodi',
'masulpani',
'dabena',
'shriguhan',
'rawas',
'khandakhoh',
'seri',
'khetauli',
'umarwah',
'chutki',
'jori',
'babouli',
'bilhama',
'chitarpur',
'sapda',
'rawai',
'chandora',
'chandraili',
'songara',
'khajuri',
'nawapara',
'deradih',
'shankarpur lipgi',
'khunshi',
'shivpur',
'rampur',
'newratola',
]

mod_path = str(Path.home().joinpath('Code','atree','scripts','WSI'))
sys.path.append(mod_path)
import indicators

print('Started!!!')

villages = {
    'CG_control': [],
    'CG_treatment': [],
    'WB_control': [],
    'WB_treatment': [],
}

for ix, df in similar_villages.iterrows():
    treatment = df['Unnamed: 0']
    control = df['village1']
    if treatment in Chattisgarh_villages:
        villages['CG_control'].append(control)
        villages['CG_treatment'].append(treatment)
    else:
        villages['WB_control'].append(control)
        villages['WB_treatment'].append(treatment)

for title, vills in villages.items():
    access_out = {}
    kharif_out = {}
    rabi_out = {}
    for year in range(start_year, end_year+1):
        roi = shrug.filter(ee.Filter.inList(unique_field, vills))
        print(f'calculating for {title} {year}')
        access_scores, kharif_area, rabi_area = indicators.access_indicator(year, roi, unique_field)
        access_out[year] = access_scores
        kharif_out[year] = kharif_area
        rabi_out[year] = rabi_area
    access_path = Path(r'C:\Users\atree\Data\WSI').joinpath(f'{title}_access_indicator.csv')
    kharif_path = Path(r'C:\Users\atree\Data\WSI').joinpath(f'{title}_kharif_area.csv')
    rabi_path = Path(r'C:\Users\atree\Data\WSI').joinpath(f'{title}_rabi_area.csv')
    pd.DataFrame(access_out).to_csv(access_path)
    pd.DataFrame(kharif_out).to_csv(kharif_path)
    pd.DataFrame(rabi_out).to_csv(rabi_path)
    print(f'completed {title}')

print('Completed!!!')
