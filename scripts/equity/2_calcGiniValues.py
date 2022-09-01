"""
Calculation of Gini coefficient for districts of chosen states or blocks of KA,
input is csv file of ET values, output of previous script.
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np
import ast


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


def main(year, fc_name, places, opPath):
    """
    python Code/atree/scripts/equity/2_calcGiniValues.py [year] [fc] [places]

    Arguments:
    year: water year provided in getETValues script. (YYYY)
    fc: "districts" or "KAblocks"
    places: two letter abbreviated state names seperated by comma or 'all' for KAblocks

    Example:
    python Code/atree/scripts/equity/2_calcGiniValues.py 2018 districts KA,TN
    python Code/atree/scripts/equity/2_calcGiniValues.py 2018 KAblocks all

    Output:
    csv file saved at Code/atree/outputs/equity
    """
    et_col = f"ET_{str(year)}"
    gini_col = f"Gini_{str(year)}"

    if fc_name == 'districts':
        places_list = places.replace("[", "").replace("]", "").split(",")
        opFilename = "_".join(places_list)
    elif fc_name == 'KAblocks':
        opFilename = 'KAblocks'
    else:
        raise ValueError(f'{fc_name} assets not found.')

    # Read pixel data
    filePath = opPath.joinpath(et_col + "_" + opFilename + ".csv")
    etTable = pd.read_csv(filePath, dtype={'places': 'category'})

    df_places = etTable.loc[:, 'places']

    # Calc Gini
    giniDict = {row['places']: gini(np.array(ast.literal_eval(
        row[et_col]), dtype='int64')) for _, row in etTable.iterrows()}
    etTable['gini'] = None

    for place in df_places:
        etTable.loc[etTable['places'] == place, 'gini'] = giniDict[place]

    filePath = opPath.joinpath(gini_col + "_" + opFilename + ".csv")

    etTable.to_csv(filePath, index=False)
    print("output: ", filePath)


if __name__ == '__main__':
    year = sys.argv[1]
    fc = sys.argv[2]  # districts or KAblocks
    places = sys.argv[3]
    root = Path.home()  # find project root
    opPath = root.joinpath("Code", "atree", "outputs", "equity")
    opPath.mkdir(parents=True, exist_ok=True)  # create if not exist
    main(year, fc, places, opPath)
