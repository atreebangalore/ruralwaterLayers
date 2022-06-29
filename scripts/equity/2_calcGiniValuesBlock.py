"""
Calculation of Gini coefficient for blocks in feature collection
input is csv file of ET values, output of 1_getETValuesBlock script.
"""

from pathlib import Path
from re import T
import sys
import pandas as pd
import numpy as np
import ast

root = Path.home()  # find project root
config = root.joinpath("Code", "atree", "config")
sys.path += [str(root), str(config)]
opPath = root.joinpath("Code", "atree", "outputs", "equity")
opPath.mkdir(parents=True, exist_ok=True)  # create if not exist
import placenames

def gini(arr):
    """Calculation of gini coefficient.

    Args:
        arr (numpy array): Array of ET values for a district.
    """
    # first sort
    sorted_arr = arr.copy()
    sorted_arr.sort()

    n = arr.size
    coef = 2. / n
    const = (n + 1.) / n
    weighted_sum = np.sum([(i+1)*yi for i, yi in enumerate(sorted_arr)])

    return round(((coef * weighted_sum / (sorted_arr.sum())) - const), 2)


def main():
    """
    python Code/atree/scripts/equity/2_calcGiniValues.py [arguments]

    Arguments:
    year: water year provided in getETValues script. (YYYY)

    Example:
    python Code/atree/scripts/equity/2_calcGiniValues.py 2018

    Output:
    csv file saved at Code/atree/outputs/equity
    """
    year = int(sys.argv[1])

    block_col = 'CD_Block_N'
    et_col = f"ET_{year}"
    gini_col = f"Gini_{year}"

    # Read pixel data
    filePath = opPath.joinpath(et_col + "_" + "blocks.csv")
    etTable = pd.read_csv(filePath, dtype={'districts': 'category'})

    districts = etTable.loc[:, 'districts']
    et = etTable.loc[:, et_col]

    # Calc Gini
    giniDict = {row['districts']: gini(np.array(ast.literal_eval(
        row[et_col]), dtype='int64')) for idx, row in etTable.iterrows()}
    etTable['gini'] = None

    for district in districts:
        etTable.loc[etTable['districts'] ==
                    district, 'gini'] = giniDict[district]

    filePath = opPath.joinpath(gini_col + "_" + 'blocks' + ".csv")

    etTable.to_csv(filePath, index=False)
    print("file saved with filename", filePath)


if __name__ == '__main__':
    main()
