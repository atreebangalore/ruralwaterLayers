"""accepts raw Landuse statistics (Classification of Area) excel file and outputs tidy dataset in CSV
input file convention is LUS_COA_[ST]_2019-20.xls

Arguments:
    state: name of state in two letters capitalized

    Example:
    python flatten_LUS_excel.py KA

    Output:
    [home dir]/Code/atree/data/lus/LUS_COA_[ST]_2019-20.csv
"""

import sys
from pathlib2 import Path
import pandas as pd

config = Path.home().joinpath("Code","atree","config")
sys.path += [str(config)]
from placenames import ST_names

def main(state: str):
    """_summary_accepts a state wise excel file from Landuse Statistics (Classification of Area)
    input filename convention is "LUS_COA_[ST]_2019-20.xls"

    Args:
        state (str): name of state in two letters capitalized
    """
    dataDir = Path.home().joinpath("Code", "atree", "data", "lus")
    filename = f'LUS_COA_{state}_2019-20'
    filepath = dataDir.joinpath('original_xls', f'{filename}.xls')
    outpath = dataDir.joinpath('CSV', f'{filename}.csv')
    dataDir.joinpath('CSV').mkdir(parents=True, exist_ok=True)
    print(filepath)

    cols = ['district',
            'reporting area for LUS',
            'forests',
            'area under non-agricultural uses',
            'barren land and unculturable land',
            'not available for cultivation total',
            'permanent pasture and other grazing land',
            'land under misc tree crops and groves not included in net area sown',
            'culturable waste land',
            'other cultivated land excluding fallow total',
            'fallow lands other than current fallows',
            'current fallows',
            'fallow land total',
            'net area sown',
            'cropped area',
            'area sown more than once']

    cols_mod = ['district',
            'LUS',
            'forests',
            'nonagricultural',
            'barren',
            'notcultivatedtotal',
            'grazing',
            'misc',
            'culturablewasteland',
            'othercultivatedtotal',
            'otherfallow',
            'currentfallow',
            'fallowtotal',
            'netareasown',
            'croppedarea',
            'sowngtonce']

    df = pd.read_excel(filepath, skiprows=[0, 1, 2], names=cols_mod)
    df.drop(df.shape[0]-1, inplace=True)
    df['district'] = df['district'].apply(lambda x: x.split('.')[-1])
    df['state'] = ST_names[state]
    df.drop(['notcultivatedtotal', 'othercultivatedtotal', 'fallowtotal'], axis=1, inplace=True)
    df.to_csv(outpath, index=False)


if __name__ == '__main__':
    state = sys.argv[1]
    main(state)
