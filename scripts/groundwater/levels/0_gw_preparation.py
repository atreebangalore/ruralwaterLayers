"""Script prepares CGWB data file from the downloaded Indiawris xls files
and after processing the file, merges the data with the historical csv file

historical csv file:
{Home Dir}/Code/atree/data/groundwater/cgwb_stationwise_historical/CGWB_original.csv
Indiawris downloaded xls files:
{Home Dir}/Code/atree/data/groundwater/downloaded_cgwb/

Returns:
    Prepared csv file at
    {Home Dir}/Code/atree/data/groundwater/Level0/CGWB_data.csv
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

root = Path.home()  # find project root
csvPath = root.joinpath("Code", "atree", "data", "groundwater",
                        "cgwb_stationwise_historical", "CGWB_original.csv")
dlPath = root.joinpath("Code", "atree", "data", "groundwater",
                       "cgwb_stationwise_historical", "downloaded_cgwb")
outPath = root.joinpath('Code', 'atree', 'data', 'groundwater', 'Level0')
outPath.mkdir(parents=True, exist_ok=True)

config = root.joinpath("Code", "atree", "config")
sys.path += [str(root), str(config)]

from placenames import ST_names
import gw_utils
import groundwater as gw_config

def clean_excel(df):
    """Cleans the raw Indiawris xls dataframe, removes the Title,
    replaces the headings

    Args:
        df (Dataframe): Indiawris xls dataframe

    Returns:
        dataframe: Cleaned Indiawris xls dataframe
    """
    df.iloc[1][df.iloc[1] ==
               'Level (m)'] = df.iloc[0]  # Level(m) to month-year
    # set new headings as column name
    df.rename(columns=df.iloc[1], inplace=True)
    df.drop(df.index[:2], inplace=True)  # drop title and line below
    colReplace = {
        'Latitude': 'LAT',
        'Longtitude': 'LON'
    }
    df.rename(colReplace, axis=1, inplace=True)  # rename LAT, LON column names
    df.reset_index(drop=True, inplace=True)
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
    """script prepares raw xls CGWB statewise data and merges with the
    Historical csv file.
    historical csv file:
    {Home Dir}/Code/atree/data/groundwater/cgwb_stationwise_historical/CGWB_original.csv
    Indiawris downloaded xls files:
    {Home Dir}/Code/atree/data/groundwater/downloaded_cgwb/

    Usage:
    python Code/atree/scripts/groundwater/level/0_gw_preparation.py

    Arguments:
    None

    Output:
    Prepared csv file at
    {Home Dir}/Code/atree/data/groundwater/Level0/CGWB_data.csv
    """
    files = [item for item in Path(dlPath).iterdir() if item.is_file()]
    conc = pd.DataFrame()  # empty DF to concat all states
    colHeadings = set()
    outFile = outPath.joinpath('CGWB_data.csv')
    for file in files:
        if file.suffix in ['.xls', '.xlsx']:
            df = pd.read_excel(file)
        elif file.suffix == '.csv':
            print(f'{file} is csv, CGWB provides data in xls')
            continue
        else:
            print(f'{file} is not recognised')
            continue
        df = clean_excel(df)
        check_state_col(file, colHeadings, set(df.columns))
        conc = conc.append(df)
    origMetacols = ["SNO", "STATE", "DISTRICT",
                    "SITE_TYPE", "WLCODE", "LON", "LAT"]
    dlMetacols = ['STATE', 'DISTRICT', 'STATION', 'LAT', 'LON', 'Station Type']
    conc = processing(conc, dlMetacols)
    conc.replace('-', np.nan, inplace=True)
    conc['STATE'] = conc['STATE'].apply(fixST)
    conc = setIndex(conc)
    # read CGWB_data.csv if it exist or else read Historical csv
    csv = pd.read_csv(outFile) if outFile.is_file() else pd.read_csv(csvPath)
    csv = processing(csv, origMetacols)
    csv = setIndex(csv)
    result = pd.concat([csv, conc], ignore_index=True, sort=False)
    result.drop(['geometry'], axis=1, inplace=True)
    result.to_csv(outFile, index=False)


if __name__ == '__main__':
    main()
