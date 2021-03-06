"""Script prepares CGWB level 1 data file from the downloaded Indiawris xls files
by cleaning and tidying them and saves in csv format.

Indiawris downloaded xls files:
{Home Dir}/Data/groundwater/levels/

Returns:
    Prepared csv file at
    {Home Dir}/Code/atree/data/groundwater/levels/level1/CGWB_levels_level1.csv
    
Improvements:
    #Efficient code: general regex rule for col name replacement
    #tobediscussed: check_state_col function necessary? - removed
"""

import itertools
import pandas as pd
import numpy as np
import sys
from pathlib import Path

homeDir = Path.home()  # Home Directory
dlPath = homeDir.joinpath("Data", "groundwater", "levels")
outPath = homeDir.joinpath('Code', 'atree', 'data',
                           'groundwater', 'levels', 'level1')
outPath.mkdir(parents=True, exist_ok=True)

config = homeDir.joinpath("Code", "atree", "config")
sys.path += [str(homeDir), str(config)]

import gw_utils
from placenames import ST_names

def clean_excel(df):
    """Takes the raw Indiawris xls dataframe and turns it into a 'tidy dataframe' 
    https://vita.had.co.nz/papers/tidy-data.pdf

    Args:
        df (Dataframe): Indiawris xls dataframe

    Returns:
        dataframe: Tidy Indiawris xls dataframe
    """
    idx = df[df.iloc[:, 0].str.match('STATE').replace(
        np.nan, False)].index.values[0]
    # headerColRow has col names like state, district, station, lat, long, station type
    headerColRow = df.iloc[idx]
    # dataColRow has col names of type 'Month YY'
    dataColRow = df.iloc[idx-1]
    dataColRow[dataColRow.isna()] = headerColRow[dataColRow.isna()]
    dataColRow = dataColRow.str.strip()
    dataColRow = dataColRow.str.replace(
        "Latitude", "LAT").replace("Longtitude", "LON")
    # set new headings as column name
    df.rename(columns=dataColRow, inplace=True)
    df.drop(df.index[:idx+1], inplace=True)  # drop title and line below
    df.reset_index(drop=True, inplace=True)
    df.replace('-', np.nan, inplace=True)
    # print(df.info())
    return df


def processing(df, metacols):
    """Preprocessing the dataframe to remove duplicates and null values

    Args:
        df (dataframe): Indiawris dataframe
        metacols (list): list of default column names

    Returns:
        dataframe: preprocessed dataframe
    """
    if set(metacols).difference(set(df.columns)):
        raise AttributeError("Columns in DataFrame doesn't match metacols")
    gwObj = gw_utils.WellDataObj(metacols=metacols, dataFrame=df)
    num_dups, num_nulls, num_geom_dups = gwObj.pre_process()
    print("after gw_utils pre-processing, df shape is:", gwObj.df.shape)
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


def checkFresh(conc, df, metacols):
    """Checks if the df to be merged already exists in conc or new

    Args:
        conc (DataFrame): Concatenated DataFrame
        df (DataFrame): DataFrame of Individual State for a year
        metacols (list): List of Constant Column Headings

    Returns:
        Boolean: True(new data) or False(already exists)
    """
    conc = conc.groupby(axis=1, level=0).sum()
    cols = (col for col in df.columns if col not in metacols)
    df.fillna(0.0, inplace=True)
    return all(all(df.at[i, c] == conc.at[i, c] for i in df.index) for c in cols)


def revertChanges(conc, df, metacols):
    """Revert back the unintended changes made to concatenated DataFrame

    Args:
        conc (DataFrame): Concatenated DataFrame
        df (DataFrame): DataFrame of Individual State for a year
        metacols (List): List of constant column headings

    Returns:
        DataFrame: Concatenated DataFrame with unintended changes reverted
    """
    for col, i in itertools.product(metacols, df.index):
        conc.loc[i, col] = df.loc[i, col]
    # Replace State Names with two letter abbreviation
    conc['STATE'] = conc['STATE'].str.strip()
    for k, v in ST_names.items():
        conc['STATE'] = conc['STATE'].str.replace(v.upper(),k)
    conc.replace(0, np.nan, inplace=True)
    return conc


def main():
    """script prepares raw xls of CGWB statewise groundwater levels data and
    concatenates into single csv file.

    Indiawris downloaded CGWB xls files:
    {Home Dir}/Data/groundwater/levels/

    Usage:
    python Code\atree\scripts\groundwater\levels\0_gw_preparation.py

    Arguments:
    None

    Output:
    Prepared csv file at
    {Home Dir}/Code/atree/data/groundwater/levels/level1/CGWB_levels_level1.csv
    """
    files = [item for item in Path(dlPath).iterdir() if item.is_file()]
    files = [f for f in files if f.suffix in [".xlsx", ".xls"]]
    files = [f for f in files if "Level Report" in str(f)]
    print('list of files acquired!')

    outFile = outPath.joinpath('CGWB_levels_level1.csv')
    if outFile.is_file():
        conc = pd.read_csv(outFile)
        conc = setIndex(conc)
    else:
        conc = pd.DataFrame()
    mCols = ['STATE', 'DISTRICT', 'STATION', 'LAT', 'LON', 'Station Type']

    # read , clean and append each xls file to conc
    for file in files:
        print(file)
        df = pd.read_excel(file, engine="openpyxl")
        df = clean_excel(df)
        df = processing(df, mCols)
        df.drop(['geometry'], axis=1, inplace=True)
        df = setIndex(df)
        df = df.loc[~df.index.duplicated(keep='first')]
        conc = pd.concat([conc, df], axis=1, ignore_index=False, sort=False)
        if checkFresh(conc, df, mCols):
            conc = conc.groupby(axis=1, level=0).sum()
        else:
            print(f'Reverting back, Part or Entire data of {file} already exist.')
            conc = conc.loc[:, ~conc.columns.duplicated()].copy()
        conc = revertChanges(conc, df, mCols)

    # use gw_utils to pre-process (remove dups)
    conc = processing(conc, mCols)
    conc.drop(['geometry'], axis=1, inplace=True)
    conc.to_csv(outFile, index=False)
    print(f'files merged to {outFile}')


if __name__ == '__main__':
    main()
