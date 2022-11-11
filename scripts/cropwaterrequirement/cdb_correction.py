import pandas as pd
from pathlib2 import Path
import os

#input
winter_change = 'Kharif'
autumn_change = 'Rabi'

original = Path.home().joinpath("Code","atree","data","crops","allcrops-allseasons-allstates-201920.csv")
out_csv = Path(os.path.dirname(os.path.realpath(__file__))).joinpath('crop_db_corrected.csv')

orig_df = pd.read_csv(original)
orig_df = orig_df.drop('perc', axis=1)
# agg_dict = {
#     'year': 'first',
#     'state': 'first',
#     'district': 'first',
#     'season': 'first',
#     'crop': 'first',
#     'area_ha': 'sum',
#     }

states = orig_df['state'].unique()
# for state in states[3:4]: # delete indexing
#     state_df = orig_df[orig_df['state']==state]
#     districts = state_df['district'].unique()
#     for district in districts[7:8]: # delete indexing
#         district_df = state_df[state_df['district']==district]
#         seasons = district_df['season'].unique()
#         if 'Winter' in seasons:
#             orig_df.loc[(orig_df['state']==state) & 
#                     (orig_df['district']==district) & 
#                     (orig_df['season']=='Winter'), 'season'] = winter_change
#             district_df.loc[(district_df['season']=='Winter'), 'season'] = winter_change
#         if 'Autumn' in seasons:
#             orig_df.loc[(orig_df['state']==state) & 
#                     (orig_df['district']==district) & 
#                     (orig_df['season']=='Autumn'), 'season'] = autumn_change
#             district_df.loc[(district_df['season']=='Autumn'), 'season'] = autumn_change
#         district_df = district_df.groupby(['crop'], as_index=False).agg(agg_dict)
#         kharif_sum = district_df.loc[district_df['season']=='Kharif', 'area_ha'].sum()
#         district_df.loc[district_df['season']=='Kharif', 'perc'] = district_df.loc[district_df['season']=='Kharif', 'area_ha']/kharif_sum
#         rabi_sum = district_df.loc[district_df['season']=='Rabi', 'area_ha'].sum()
#         district_df.loc[district_df['season']=='Rabi', 'perc'] = district_df.loc[district_df['season']=='Rabi', 'area_ha']/rabi_sum

orig_df['season'] = orig_df['season'].str.replace('Winter', winter_change).str.replace('Autumn', autumn_change)
orig_df = orig_df.groupby(['year', 'state', 'district', 'season', 'crop'], as_index=False).agg({'area_ha': 'sum'})
# print(orig_df)
# print(orig_df.shape)

for state in states:
    districts = orig_df[orig_df['state']==state]['district'].unique()
    for district in districts:
        kharif_sum = orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Kharif'), 'area_ha'].sum()
        orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Kharif'), 'perc'] = orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Kharif'), 'area_ha']/kharif_sum
        rabi_sum = orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Rabi'), 'area_ha'].sum()
        orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Rabi'), 'perc'] = orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Rabi'), 'area_ha']/rabi_sum
        summer_sum = orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Summer'), 'area_ha'].sum()
        orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Summer'), 'perc'] = orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Summer'), 'area_ha']/summer_sum
        whole_yr_sum = orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Whole Year'), 'area_ha'].sum()
        orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Whole Year'), 'perc'] = orig_df.loc[(orig_df['state']==state) & (orig_df['district']==district) & (orig_df['season']=='Whole Year'), 'area_ha']/whole_yr_sum

orig_df['perc'] = round(orig_df['perc']*100,0)

orig_df.to_csv(out_csv, index=False)