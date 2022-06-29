"""
accepts a state wise excel file with all crops and all seasons and returns a "tidy dataset"
input filename convention is "allcrops-allseasons-[ST]-201920.xls"

"""

import os,sys
from pathlib import Path
import pandas as pd

dataDir = Path.home().joinpath("Code","atree","data")
os.chdir(dataDir)



def main():
    """
    accepts a state wise excel file with all crops and all seasons and returns a "tidy dataset"
    input filename convention is "allcrops-allseasons-[ST]-201920.xls"
    
    Arguments:
    state: name of state in two letters capitalized

    Example:
    python flattenCropsExcel.py KA

    Output:
    crops/allcrops-allseasons-[ST]-201920.csv

    """

    state = sys.argv[1]

    filename = "allcrops-allseasons-" + state + "-201920.xls"
    filepath = dataDir.joinpath("crops",filename)
    print(filepath)

    # define column names and datatypes
    cols = ['district','year','season','area_ha','production_tonnes','yield_tonnes_ha']
    # dtype = {'district':str,'year':str,'season':str,'area_ha':float,'production_tonnes':float,'yield_tonnes_ha':float}

    # instantiate df
    df = pd.read_excel(filepath,skiprows=[0,1,3],names=cols)

    # the excel files come with many rows blank, these can be filled using forward fill method

    # year
    df['year'] = df['year'].fillna(method='ffill')

    # crop
    df['crop'] = df[df.loc[:,"season"].isna()]['district']
    df['crop'] = df['crop'].str.replace("-","").str.replace("Total ","").str.replace(" ","") ## Better way???
    df['crop'] = df['crop'].fillna(method='ffill')

    # season
    df.dropna(subset=['season'],inplace=True)

    # district
    df['district'] = df['district'].fillna(method='ffill')
    df = df.loc[df.season!="Total",:]
    df['district'] = df['district'].str.replace(r'[0-9]','',regex=True).str.replace(".","",regex=False)

    # sort df
    df = df.loc[:,['year','district','season','crop','area_ha']]
    df.sort_values(['district','season'],inplace=True)

    # add perc value
    df['perc'] = (df.area_ha / df.groupby(['district','season'])['area_ha'].transform('sum') * 100).round().astype('int')

    # save file to csv
    df.to_csv("crops/allcrops-allseasons-" + state + "-201920.csv",index=False)



if __name__=='__main__':
    main()
