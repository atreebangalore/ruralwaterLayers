"""
Extraction of district wise ET pixel values for blocks in feature collection
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
opPath = root.joinpath("Code", "atree", "outputs", "equity")
opPath.mkdir(parents=True, exist_ok=True)  # create if not exist
import placenames

def main():
    """
    python Code/atree/scripts/equity/1_getETValues.py [arguments]

    Arguments:
    year: water year for Image filter. (YYYY)

    Example:
    python Code/atree/scripts/equity/1_getETValues.py 2018

    Output:
    csv file saved at Code/atree/outputs/equity
    """
    year = int(sys.argv[1])

    block_col = 'CD_Block_N'

    et_col = f"ET_{year}"

    start = ee.Date.fromYMD(year, 6, 1)
    end = ee.Date.fromYMD(year+1, 5, 31)

    ############         Boundary Polygon        #################
    boundaries = ee.FeatureCollection(
        "users/jaltol/FeatureCol/Karnataka_Block_Typologies_2015_2020")

    ############         Image Collection        #################
    iColl = ee.ImageCollection("users/jaltol/ET_new/etSSEBop")
    iColl_filtered = iColl.filterDate(start, end)
    proj = iColl_filtered.first().projection()
    scale = proj.nominalScale()
    image = iColl_filtered.reduce(ee.Reducer.sum())

    pixDict = image.reduceRegions(
        collection=boundaries,
        reducer=ee.Reducer.toList(),
        scale=scale,
        crs=proj
    )

    pixDict = pixDict.select([block_col, "list"], [
                             block_col, et_col], False).getInfo()
    blocks = [elem['properties'][block_col] for elem in pixDict['features']]
    pixValues = [elem['properties'][et_col] for elem in pixDict['features']]

    etTable = pd.DataFrame({'districts': blocks, et_col: pixValues})
    filePath = opPath.joinpath(et_col + "_" + 'blocks' + ".csv")

    etTable.to_csv(filePath, index=False)
    print("file saved with filename", filePath)


if __name__ == '__main__':
    main()
