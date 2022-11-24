import pandas as pd
import os,sys
from pathlib import Path
from collections import defaultdict
import logging

import ee
ee.Initialize()

root = Path.home().joinpath("Code","atree")
sys.path.append(root)

from config.gee_assets import fCol
from fao import CWR, CropDetails
logging.basicConfig(filemode='w')

dist2011 = fCol['dist2011']

majority_ag_fpath = Path.home().joinpath("Code","atree","data","crops","majority_ag_dw_80p.csv")
majority_ag = pd.read_csv(majority_ag_fpath)
majority_ag = majority_ag.sort_values(['state','District'])
majority_ag['District'] = majority_ag['District'].str.lower()

# TO REVIEW DISTRICT NAMES IN DW/2011 Districts
# logging.info("\nDynamic World districts")
dw_dist = defaultdict(list)
for idx,row in majority_ag[['state','District']].iterrows():
    dw_dist[row['state']].append(row['District'])
# for st in list(dw_dist.keys()):
    # logging.info(st,"\n",dw_dist[st])    

# crop_db_fpath = Path.home().joinpath("Code","atree","data","crops","allcrops-allseasons-allstates-201920.csv")
crop_db_fpath = Path(os.path.dirname(os.path.realpath(__file__))).joinpath('crop_db_corrected.csv')
cropdb = pd.read_csv(crop_db_fpath)
cropdb = cropdb.sort_values(['state','district'])
cropdb['district'] = cropdb['district'].str.lower()

# TO REVIEW DISTRICT NAMES IN CROP APY
# logging.info("\nCrop APY districts")
apy_dist = defaultdict(list)
for idx,row in cropdb[['state','district']].iterrows():
    if row['district'] not in apy_dist[row['state']]:
        apy_dist[row['state']].append(row['district'])
# for st in list(dw_dist.keys()):
    # logging.info(st,"\n",apy_dist[st])    

season_list = ['Kharif', 'Rabi', 'Summer']#, 'Whole Year']

# for _,row in majority_ag.iloc[1:2,:].iterrows():
def get_detail(st, dst, outputfile):
    year = 2019
    # st = row['state'].title()
    # dst = row['District'].title()
    ETc_crops = defaultdict(dict)
    ETc_months = defaultdict(dict)
    ETc_months['Areas'] = {}

    for season in season_list:
        filtered_cropdb = cropdb[(cropdb['state']==st) & (cropdb['district']==dst) & (cropdb['season']==season)]
        geometry = dist2011.filter(ee.Filter.And(ee.Filter.eq('ST_NM',st),ee.Filter.eq('DISTRICT',dst))).first().geometry()
        crop_details = CropDetails(2019, st, dst, season, geometry)
        crop_dict = crop_details.get_crop_details(7)    # {'crop':(area_ha, area%, sowing_date, KcList, GrowthPeriodList)}
        total_area = round(crop_dict['total_area']) * 10000
        crop_dict.pop('total_area',None)

        district_logger.info(f"\n***** Crop Dictionary  {season}*****")
        for k,v in crop_dict.items():
            district_logger.info(f'{k} : {v[0]} Ha')
        district_logger.info(f"\ntotal District Cropland area (Ha) {(total_area/1e4):,}")

        cwr = CWR(year,crop_dict)

        refET = cwr.get_refET(geometry)

        #Does this need to be repeated per season?
        district_logger.info(f"\n*****  ref ET - {season} (mm/day) *****") 
        district_logger.info(f'{refET}')

        kc_mo = cwr.get_Kc_monthly()

        district_logger.info(f"\n*****  kc monthly - {season} *****")
        for k,v in kc_mo.items():
            district_logger.info(f'{k} : {v}')

        ETc_mm_crops, ETc_crops[season], ETc_months[season] = cwr.get_ETc()
        district_logger.info(f"\n======== ETc crop wise - {season} (mm) =======")
        for crop, mm_value in ETc_mm_crops.items():
            total = mm_value['total']
            district_logger.info(f'{crop} : {total:,}')

        district_logger.info(f"\n*****  ETc Crop Wise - {season} (m3) *****")
        for crop,monthly_dict in ETc_crops[season].items():
            total = monthly_dict['total']
            district_logger.info(f'{crop} : {total:,}')

        district_logger.info(f"\n*****  ET Month Wise - {season} (m3) *****")
        for month,crop_dict in ETc_months[season].items():
            total = crop_dict['total']
            if total > 0:
                ETc_months['Areas'].update({month:total_area})
            district_logger.info(f'{month} : {total:,}')

        district_logger.info(f"\n*****  ET Month Wise - {season} (mm)  *****")
        for month,crop_dict in ETc_months[season].items():
            total = int(round(crop_dict['total'] / total_area,3) * 1e3)
            district_logger.info(f'{month} : {total}')
        
    keys = ['06','07','08','09','10','11','12','01','02','03','04','05']
    ETc_months['All'] = {}
    for month in keys:
        ETc_months['All'].update({month:{'total':0}})
        for season in season_list:
            ETc_months['All'][month]['total'] += ETc_months[season][month]['total']
    
    district_logger.info("\n*****  ET Month Wise - All months (m3) *****")
    for month,crop_dict in ETc_months['All'].items():
        total = crop_dict['total']
        district_logger.info(f'{month} : {total:,}')

    district_logger.info("\n***** ET Month Wise - All months (mm)  *****")
    out_dict = {}
    for month,crop_dict in ETc_months['All'].items():
        if crop_dict['total'] > 0:
            total = int(round(crop_dict['total'] / ETc_months['Areas'][month],3) * 1e3)
            district_logger.info(f'{month} : {total}')
            if month in [f'{i:02d}' for i in range(6,13)]:
                out_dict[f'{year}{month}'] = {'ETc(mm)': total}
            else:
                out_dict[f'{year+1}{month}'] = {'ETc(mm)': total}
    out_df = pd.DataFrame(out_dict)
    out_df.to_csv(outputfile, index=False)

if __name__=='__main__':
    state = 'Bihar'
    district = 'Buxar'
    district_logger = logging.getLogger()
    district_logger.setLevel(logging.INFO)
    district_fHandler = logging.FileHandler(str(Path(os.path.dirname(os.path.realpath(__file__))).joinpath('outputs', f'{state}_{district}.log')))
    district_fHandler.setLevel(logging.INFO)
    district_sHandler = logging.StreamHandler()
    district_sHandler.setLevel(logging.INFO)
    district_logger.addHandler(district_fHandler)
    district_logger.addHandler(district_sHandler)
    out_path = Path(os.path.dirname(os.path.realpath(__file__))).joinpath('outputs', f'{state}_{district}.csv')
    get_detail(state, district, out_path)