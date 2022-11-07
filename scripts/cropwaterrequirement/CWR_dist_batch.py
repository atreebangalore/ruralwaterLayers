import pandas as pd
import os,sys
from pathlib import Path
from collections import defaultdict

import ee
ee.Initialize()

root = Path.home().joinpath("Code","atree")
sys.path.append(root)

from config.gee_assets import fCol
from fao import CWR, CropDetails

dist2011 = fCol['dist2011']

majority_ag_fpath = Path.home().joinpath("Code","atree","data","crops","majority_ag_dw_80p.csv")
majority_ag = pd.read_csv(majority_ag_fpath)
majority_ag = majority_ag.sort_values(['state','District'])
majority_ag['District'] = majority_ag['District'].str.lower()

# TO REVIEW DISTRICT NAMES IN DW/2011 Districts
# print("\nDynamic World districts")
dw_dist = defaultdict(list)
for idx,row in majority_ag[['state','District']].iterrows():
    dw_dist[row['state']].append(row['District'])
# for st in list(dw_dist.keys()):
    # print(st,"\n",dw_dist[st])    

crop_db_fpath = Path.home().joinpath("Code","atree","data","crops","allcrops-allseasons-allstates-201920.csv")
cropdb = pd.read_csv(crop_db_fpath)
cropdb = cropdb.sort_values(['state','district'])
cropdb['district'] = cropdb['district'].str.lower()

# TO REVIEW DISTRICT NAMES IN CROP APY
# print("\nCrop APY districts")
apy_dist = defaultdict(list)
for idx,row in cropdb[['state','district']].iterrows():
    if row['district'] not in apy_dist[row['state']]:
        apy_dist[row['state']].append(row['district'])
# for st in list(dw_dist.keys()):
    # print(st,"\n",apy_dist[st])    

season_list = ['Kharif', 'Rabi', 'Summer', 'Whole Year']

for _,row in majority_ag.iloc[:1,:].iterrows():
    year = 2019
    st = row['state'].title()
    dst = row['District'].title()
    ETc_crops = defaultdict(dict)
    ETc_months = defaultdict(dict)
    ETc_months['Areas'] = {}

    for season in season_list[:2]:
        filtered_cropdb = cropdb[(cropdb['state']==st) & (cropdb['district']==dst) & (cropdb['season']==season)]
        geometry = dist2011.filter(ee.Filter.And(ee.Filter.eq('ST_NM',st),ee.Filter.eq('DISTRICT',dst))).first().geometry()
        crop_details = CropDetails(2019, st, dst, season, geometry)
        crop_dict = crop_details.get_crop_details(7)    # {'crop':(area_ha, area%, sowing_date, KcList, GrowthPeriodList)}
        total_area = round(crop_dict['total_area']) * 10000
        crop_dict.pop('total_area',None)

        # print("\n***** Crop Dictionary  *****")
        for k,v in crop_dict.items():
            print(k,":",v[0]," Ha")
        print("\ntotal District Cropland area (Ha) ",f'{(total_area/1e4):,}')

        cwr = CWR(year,crop_dict)

        refET = cwr.get_refET(geometry)

        #Does this need to be repeated per season?
        # print("\n*****  ref ET - " + season + " (mm/day) *****") 
        # print(refET)

        kc_mo = cwr.get_Kc_monthly()

        # print("\n*****  kc monthly - " + season + " *****")
        # for k,v in kc_mo.items():
            # print(k,":",v)

        ETc_crops[season], ETc_months[season] = cwr.get_ETc()

        print("\n*****  ETc Crop Wise - " + season + " (m3) *****")
        for crop,monthly_dict in ETc_crops[season].items():
            total = monthly_dict['total']
            print(crop,":",f'{total:,}')

        print("\n*****  ET Month Wise - " + season + " (m3) *****")
        for month,crop_dict in ETc_months[season].items():
            total = crop_dict['total']
            if total > 0:
                ETc_months['Areas'].update({month:total_area})
            print(month,":",f'{total:,}')

        print("\n*****  ET Month Wise - " + season + " (mm)  *****")
        for month,crop_dict in ETc_months[season].items():
            total = int(round(crop_dict['total'] / total_area,3) * 1e3)
            print(month,":",total)
        
    keys = ['06','07','08','09','10','11','12','01','02','03','04','05']
    ETc_months['All'] = {}
    for month in keys:
        ETc_months['All'].update({month:{'total':0}})
        for season in season_list[0:2]:
            ETc_months['All'][month]['total'] += ETc_months[season][month]['total']
    
    print("\n*****  ET Month Wise - All months (m3) *****")
    for month,crop_dict in ETc_months['All'].items():
        total = crop_dict['total']
        print(month,":",f'{total:,}')

    print("\n***** ET Month Wise - All months (mm)  *****")
    for month,crop_dict in ETc_months['All'].items():
        if crop_dict['total'] > 0:
            total = int(round(crop_dict['total'] / ETc_months['Areas'][month],3) * 1e3)
            print(month,":",total)
