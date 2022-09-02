"""
Extraction of district wise ET pixel values for chosen States or blocks of KA
with the SEBOP annual ET image (from GEE) as input.
"""
from pathlib import Path
import ee
import sys
import pandas as pd
ee.Initialize()

root = Path.home()  # find project root
config = root.joinpath("Code", "atree", "config")
sys.path += [str(root), str(config)]
import geeassets
import placenames
from geeassets import fCollDict as fcd


def main(year, fc_name, places, opPath, roi=None):
    """
    python Code/atree/scripts/equity/1_getETValues.py [year] [fc] [places] [roi]

    Arguments:
    year: water year for Image filter. (YYYY)
    fc: "districts" or "KAblocks"
    places: two letter abbreviated state names seperated by comma or 'all' for KAblocks
    roi (optional): CA or NCA - clip to KA command area or non command area

    Example:
    python Code/atree/scripts/equity/1_getETValues.py 2018 districts KA,TN
    python Code/atree/scripts/equity/1_getETValues.py 2018 KAblocks all CA

    Output:
    csv file saved at Code/atree/outputs/equity
    """
    et_col = f"ET_{str(year)}"
    start = ee.Date.fromYMD(int(year), 6, 1)
    end = ee.Date.fromYMD(int(year)+1, 5, 31)

    ############         Boundary Polygon        #################
    if fc_name == 'districts':
        places_list = places.replace("[", "").replace("]", "").split(",")
        opFilename = "_".join(places_list)
        boundaries = fcd[fc_name]['id']
        state_col = fcd[fc_name]['state_col']
        required_col = fcd[fc_name]['district_col']
        chosen_states = [placenames.ST_names[state] for state in places_list]
        boundaries = boundaries.filter(
            ee.Filter.inList(state_col, chosen_states))
    elif fc_name == 'KAblocks':
        boundaries = fcd[fc_name]['id']
        required_col = fcd[fc_name]['block_col']
        opFilename = 'KAblocks'
        roi_dict = dict(CA=fcd['KAcommandarea']['id'],NCA=fcd['KAnoncommandarea']['id'])
    else:
        raise ValueError(f'{fc_name} assets not found.')

    ############         Image Collection        #################
    iColl = geeassets.iCollDict['evapotranspiration']
    iColl_filtered = iColl.filterDate(start, end)
    proj = iColl_filtered.first().projection()
    scale = proj.nominalScale()
    image = iColl_filtered.reduce(ee.Reducer.sum())
    if roi and fc_name == 'KAblocks':
        image = image.clip(roi_dict[roi])

    pixDict = image.reduceRegions(
        collection=boundaries,
        reducer=ee.Reducer.toList(),
        scale=scale,
        crs=proj
    )

    pixDict = pixDict.select([required_col, "list"], [
                             required_col, et_col], False).getInfo()
    districts = [elem['properties'][required_col]
                 for elem in pixDict['features']]
    pixValues = [elem['properties'][et_col] for elem in pixDict['features']]

    etTable = pd.DataFrame({'places': districts, et_col: pixValues})
    filePath = opPath.joinpath(et_col + "_" + opFilename + ".csv")

    etTable.to_csv(filePath, index=False)
    print("output: ", filePath)


if __name__ == '__main__':
    year = sys.argv[1]
    fc = sys.argv[2]  # districts or KAblocks
    places = sys.argv[3]
    try:
        roi = sys.argv[4] # CA or NCA
    except IndexError:
        roi = None
    opPath = root.joinpath("Code", "atree", "outputs", "equity")
    opPath.mkdir(parents=True, exist_ok=True)  # create if not exist
    main(year, fc, places, opPath, roi)
