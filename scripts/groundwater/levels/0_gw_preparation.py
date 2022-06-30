import pandas as pd
import sys
from pathlib import Path

root = Path.home() # find project root
csv = root.joinpath("Code","atree","data","groundwater","cgwb_stationwise_historical","CGWB_original.csv")
dlPath = root.joinpath("Code","atree","data","groundwater","downloaded_cgwb")

config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]

import groundwater as gw_config

def clean_excel(df):
    df.iloc[1][df.iloc[1]=='Level (m)']=df.iloc[0]
    df.rename(columns=df.iloc[1], inplace = True)
    df.drop(df.index[:2], inplace = True)
    df.reset_index(drop=True, inplace=True)
    return df

def check_state_col(file,colHeadings,colSet):
    if colHeadings:
        if colSet.intersection(colHeadings):
            print(f"{file}:mismatch in Column Headings")
    else:
        colHeadings = colSet

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
        else:
            print(f'{file} is not recognised')
            continue
        df = clean_excel(df)
        check_state_col(file,colHeadings,set(df.columns))
        conc = conc.append(df)
    print(conc.columns)

if __name__=='__main__':
    main()