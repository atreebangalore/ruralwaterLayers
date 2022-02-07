"""
Don't know yet
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np

root = Path.home() # find project root
sys.path.append(str(root))    # this allows lib and config modules below to be found
opPath = root.joinpath("Code","atree","outputs","groundwater","micensus")
print("data saved in :",opPath)

def main():
    """
    """
    state = "MH"
    census_path = root.joinpath("Data","census","DCHB_Village_Release_"+state+".csv")
    print(census_path)
    
    col_list = ["District Code","District Name",
               "Sub District Code","Sub District Name",
               "Village Code","Village Name"]
    dfc = pd.read_csv(census_path,usecols=col_list)
    print(dfc.head())
    
    micensus_path = root.joinpath("Data","micensus","2013-14","mi_census5_13-14_Depth_Dugwells.csv")
    mic = pd.read_csv(micensus_path)
    print(mic.head(),mic.columns)
    
    
    
    
    
if __name__=='__main__':
    main()