import pandas as pd
import sys
from pathlib import Path

root = Path.home() # find project root
csvPath = root.joinpath("Code","atree","data","groundwater","cgwb_stationwise_historical","CGWB_original.csv")
dlPath = root.joinpath("Code","atree","data","groundwater","downloaded_cgwb")

config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]

import groundwater as gw_config
import gw_utils

def clean_excel(df):
    df.iloc[1][df.iloc[1]=='Level (m)']=df.iloc[0]
    df.rename(columns=df.iloc[1], inplace = True)
    df.drop(df.index[:2], inplace = True)
    colReplace = {
        'Latitude': 'LAT',
        'Longtitude': 'LON'
    }
    df.rename(colReplace, axis=1, inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

def check_state_col(file,colHeadings,colSet):
    if colHeadings:
        if colSet.difference(colHeadings):
            raise Exception(f"{file}:mismatch in Column Headings")
        # sourcery skip: raise-specific-error
    else:
        colHeadings = colSet

def processing(df,metacols):
    gwObj = gw_utils.WellDataObj(metacols=metacols,dataFrame=df)
    num_dups,num_nulls,num_geom_dups = gwObj.pre_process()
    return gwObj.df

def main():
    """script prepares raw xls CGWB statewise data and merges with the
    Historical csv file.
    """
    files = [item for item in Path(dlPath).iterdir() if item.is_file()]
    conc = pd.DataFrame() # empty DF to concat all states
    colHeadings = set()
    for file in files:
        if file.suffix in ['.xls','.xlsx']:
            df = pd.read_excel(file)
        elif file.suffix == '.csv':
            print(f'{file} is csv, CGWB provides data in xls')
            continue
        else:
            print(f'{file} is not recognised')
            continue
        df = clean_excel(df)
        check_state_col(file,colHeadings,set(df.columns))
        conc = conc.append(df)
    origMetacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    dlMetacols = ['STATE', 'DISTRICT', 'STATION', 'LAT', 'LON', 'Station Type']
    conc = processing(conc,dlMetacols)
    # conc.rename({'Latitude': 'LAT', 'Longtitude': 'LON'}, axis=1, inplace=True)
    conc['latlon'] = conc['LAT'].astype(str)+','+conc['LON'].astype(str)
    conc.set_index('latlon', inplace = True)
    csv = pd.read_csv(csvPath)
    csv = processing(csv,origMetacols)
    csv['latlon'] = csv['LAT'].astype(str)+','+csv['LON'].astype(str)
    csv.set_index('latlon', inplace = True)
    result = pd.concat([csv, conc], ignore_index=True, sort=False)
    # result = pd.merge(csv, conc, on=['latlon','STATE','DISTRICT','LAT','LON'], how="outer")
    # result = pd.merge(csv, conc, on="latlon", how="outer")
    result.to_csv(r'C:\Users\atree\Code\atree\data\groundwater\downloaded_cgwb\test.csv')

if __name__=='__main__':
    main()