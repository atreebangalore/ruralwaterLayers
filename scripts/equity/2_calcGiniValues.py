"""
Given the ET Values in a CSV, calculate Gini for chosen districts
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np
import ast

root = Path.home() # find project root
config = root.joinpath("Code","atree","config")
sys.path += [str(root),str(config)]
opPath = root.joinpath("Code","atree","outputs","equity")
print("data saved in :",opPath)

import placenames

def gini(arr):
    ## first sort
    sorted_arr = arr.copy()
    sorted_arr.sort()
    
    n = arr.size
    coef = 2. / n
    const = (n + 1.) / n
    weighted_sum = np.sum([(i+1)*yi for i, yi in enumerate(sorted_arr)])
    
    return round(((coef * weighted_sum / (sorted_arr.sum())) - const),2)

def main():
    """
    """
    year = int(sys.argv[1])
    states = sys.argv[2].replace("[","").replace("]","").split(",")
    states_str = "_".join(states)
    
    state_col = placenames.datameet_state_col_name
    district_col = placenames.datameet_district_col_name
    et_col = "ET_" + str(year)
    gini_col = "Gini_" + str(year)

    # Read pixel data
    filePath = opPath.joinpath(et_col + "_" + states_str + ".csv")
    etTable = pd.read_csv(filePath,dtype={'districts':'category'})
#     print(etTable.info(),etTable.head())
    
    districts = etTable.loc[:,'districts']
    et = etTable.loc[:,et_col]
#     etDict = {row['districts']:row[et_col] for idx,row in etTable.iterrows()}
#     print(etDict.keys())
    
    # Calc Gini
    giniDict = {row['districts']:gini(np.array(ast.literal_eval(row[et_col]),dtype='int64')) for idx,row in etTable.iterrows()}
    etTable['gini'] = None
    
    for district in districts:
        etTable.loc[etTable['districts']==district,'gini'] = giniDict[district]
        
    filePath = opPath.joinpath(gini_col + "_" + states_str + ".csv")
    print("file saved with filename",filePath)
    
    etTable.to_csv(filePath,index=False)
    
if __name__=='__main__':
    main()