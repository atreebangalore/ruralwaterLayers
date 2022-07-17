"""Script prepares CGWB data file from the downloaded Indiawris xls files
and after processing the file

Indiawris downloaded xls files:
{Home Dir}/Code/atree/data/groundwater/cgwb_stationwise_historical/downloaded_cgwb/

Returns:
    Prepared csv file at
    {Home Dir}/Code/atree/data/groundwater/levels/level1/cgwb_all.csv
    
Improvements:
    #Efficient code: general regex rule for col name replacement
    #tobediscussed: check_state_col function necessary?
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

root = Path.home()  # find project root
dlPath = root.joinpath("Data","groundwater","levels")  # contains single file per state per year
outPath = root.joinpath('Code', 'atree', 'data', 'groundwater','levels', 'level1')
outPath.mkdir(parents=True, exist_ok=True)

config = root.joinpath("Code", "atree", "config")
sys.path += [str(root), str(config)]

from placenames import ST_names
import gw_utils
import groundwater as gw_config

def clean_excel(df):
    """Takes the raw Indiawris xls dataframe and turns it into a 'tidy dataframe' 
    https://vita.had.co.nz/papers/tidy-data.pdf

    Args:
        df (Dataframe): Indiawris xls dataframe

    Returns:
        dataframe: Tidy Indiawris xls dataframe
    """
    idx = df[df.iloc[:,0].str.match('STATE').replace(np.nan,False)].index.values[0]
    # headerColRow has col names like state, district, station, lat, long, station type
    headerColRow = df.iloc[idx]
    # dataColRow has col names of type 'Month YY'
    dataColRow = df.iloc[idx-1]
    dataColRow[dataColRow.isna()] = headerColRow[dataColRow.isna()]
    dataColRow = dataColRow.str.replace("Latitude","LAT").replace("Longtitude","LON") 
    # set new headings as column name
    df.rename(columns=dataColRow, inplace=True)
    df.drop(df.index[:idx+1], inplace=True)  # drop title and line below
    df.reset_index(drop=True, inplace=True)
    df.replace('-', np.nan, inplace=True)
    print(df.info())
    return df


def check_state_col(file, colHeadings, colSet):
    """Checks whether the headings of all dataframes are similar so as to 
    prevent error while concatenation

    Args:
        file (Path): path to the Indiawris xls file
        colHeadings (set): column names to be checked with
        colSet (set): column names of the current dataframe

    Raises:
        ValueError: if Column Headings doesnot match (not of same year)
    """
    if colHeadings:
        if colSet.difference(colHeadings):
            raise ValueError(f"{file}:Column Headings of downloaded files not \
similar, do one time period at a time")
    else:
        colHeadings = colSet


def processing(df, metacols):
    """Preprocessing the dataframe to remove duplicates and null values

    Args:
        df (dataframe): Indiawris dataframe
        metacols (list): list of default column names

    Returns:
        dataframe: preprocessed dataframe
    """
    gwObj = gw_utils.WellDataObj(metacols=metacols, dataFrame=df)
    num_dups, num_nulls, num_geom_dups = gwObj.pre_process()
    print("after gw_utils pre-processing, df shape is:",gwObj.df.shape)
    return gwObj.df


def setIndex(df):
    """create a latlon column and make it index

    Args:
        df (dataframe): Indiawris or Historical dataframe

    Returns:
        dataframe: dataframe ready for concatenation
    """
    df['latlon'] = df['LAT'].astype(str)+','+df['LON'].astype(str)
    df.set_index('latlon', inplace=True)
    return df


def fixST(name):
    """STATE Column values into two letter abbreviation

    Args:
        name (string): state name from the STATE column

    Returns:
        string: Two letter abbreviated state name
    """
    return next((k for k, v in ST_names.items() if v.upper() == name.upper()), name)


def main():
    """script prepares raw xls of CGWB statewise groundwater levels data and concatenates into single csv file.
    
    Indiawris downloaded CGWB xls files:
    {Home Dir}/Data/groundwater/levels/

    Usage:
    python Code\atree\scripts\groundwater\levels\0_gw_preparation.py

    Arguments:
    None

    Output:
    Prepared csv file at
    {Home Dir}/Code/atree/data/groundwater/level1/CGWB_data.csv
    """
    files = [item for item in Path(dlPath).iterdir() if item.is_file()]
    files = [f for f in files if (f.suffix==".xlsx" or f.suffix==".xls")]
    files = [f for f in files if "LevelReport" in str(f)]
    
    conc = pd.DataFrame()  # empty DF to concat all states
    colHeadings = set()
    outFile = outPath.joinpath('CGWB_levels_level1.csv')
    
    # read , clean and append each xls file to conc
    for file in files[0:1]:
        df = pd.read_excel(file,engine="openpyxl")
        df = clean_excel(df)
#         check_state_col(file, colHeadings, set(df.columns))
        conc = conc.append(df)
    
    # use gw_utils to pre-process (remove dups)
    origMetacols = ["SNO", "STATE", "DISTRICT",
                    "SITE_TYPE", "WLCODE", "LON", "LAT"]
    dlMetacols = ['STATE', 'DISTRICT', 'STATION', 'LAT', 'LON', 'Station Type']
    conc = processing(conc, dlMetacols)
#     conc['STATE'] = conc['STATE'].apply(fixST)
#     conc = setIndex(conc)
    conc.to_csv(outFile,index=False)
#     # read CGWB_data.csv if it exist or else read Historical csv
#     csv = pd.read_csv(outFile) if outFile.is_file() else pd.read_csv(csvPath)
#     csv = processing(csv, origMetacols)
#     csv = setIndex(csv)
#     result = pd.concat([csv, conc], ignore_index=True, sort=False)
#     result.drop(['geometry'], axis=1, inplace=True)
#     result.to_csv(outFile, index=False)


if __name__ == '__main__':
    main()
