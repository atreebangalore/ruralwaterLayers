"""Get IITB evapotranspiration data
source: Jaltol IITB ET GEE collection
IITB ET is a 8 day avg data, so filling the 8 days is done to get
daily data.
script to be performed in QGIS with shp added as layer.

Returns:
    CSV: CSV of daily IITB ET data
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import json
import qgis
from qgis.core import QgsJsonExporter
from typing import Tuple, Dict
import ee
ee.Initialize()


def get_feature_collection(active_lyr: qgis._core.QgsVectorLayer) -> ee.FeatureCollection:
    """convert the input layer to ee.Feature Collection

    Args:
        active_lyr (vector_layer): active layer from the iface

    Returns:
        ee.FeatureCollection: Earth Engine Feature Collection object of the layer
    """
    lyr = QgsJsonExporter(active_lyr)
    gs = lyr.exportFeatures(active_lyr.getFeatures())
    gj = json.loads(gs)
    for feature in gj['features']:
        feature['id'] = f'{feature["id"]:04d}'
    return ee.FeatureCollection(gj)


def get_image(date: datetime) -> ee.Image:
    """filter image collection for a single day.

    Args:
        date (datetime): date for which image is required

    Returns:
        ee.Image: ee.Image corresponding to the date
    """
    image = i_coll.filterDate(
        f'{date:%Y-%m-%d}', f'{(date+timedelta(days=1)):%Y-%m-%d}')
    return image.first().updateMask(image.first().gte(0))


def calc(feature: ee.Feature, image: ee.Image) -> Tuple[str, Dict[str, float]]:
    """calculate statistic for the provided feature with the image

    Args:
        feature (ee.Feature): boundary to calc statistics
        image (ee.Image): image from which statistics are calculated

    Returns:
        Tuple[str, Dict[str, float]]: unique col value, band stats in dict
    """
    name = feature.getInfo()['properties'][col_name]
    params = {
        'reducer': ee.Reducer.mean(),
        'geometry': feature.geometry(),
        'scale': 5000,
        'maxPixels': 1e12
    }
    result = image.reduceRegion(**params).getInfo()
    return name, result


def get_data(f_col_list: ee.List, f_col_size: int, image: ee.Image) -> Dict[str, float]:
    """get the ET data in dict format for a specific image.

    Args:
        f_col_list (ee.List): list of features
        f_col_size (int): size of the feature collection
        image (ee.Image): image for the day

    Returns:
        Dict[str, float]: Dict with unique field value as key and ET as value
    """
    data_dict = {}
    # for num in range(f_col_size):
    # feature = ee.Feature(f_col_list.get(num))
    with ThreadPoolExecutor() as ex:
        futures = [ex.submit(calc, ee.Feature(f_col_list.get(num)), image)
                   for num in range(f_col_size)]

    for future in as_completed(futures):
        # final.append(future.result())
        name, result = future.result()
        data_dict[name] = result['b1']
    return data_dict


def main(source_lyr: qgis._core.QgsVectorLayer):
    """get IITB ET daily data, run this script inside QGIS.
    change the input section below as needed.

    Args:
        source_lyr (qgis._core.QgsVectorLayer): layer in QGIS
    """
    lyr_name = source_lyr.name()
    print(f'{lyr_name}, {orig_date:%Y%m%d}')

    # source_lyr = iface.activeLayer()
    f_col = get_feature_collection(source_lyr)
    f_col_size = f_col.size().getInfo()
    f_col_list = f_col.toList(f_col_size)

    image = get_image(orig_date)
    data = get_data(f_col_list, f_col_size, image)
    # print(data)

    output_dict = {}
    for date in dates_list:
        date_str = f'{date:%Y%m%d}'
        month = date.strftime("%b")
        print(f'{lyr_name}, {date_str}')
        if date_str in IITB_dates:
            image = get_image(date)
            data = get_data(f_col_list, f_col_size, image)
        output_dict[date_str] = data
        output_dict[date_str].update({'month': month})

    # print(output_dict)
    df = pd.DataFrame(output_dict).T
    df.to_csv(out_dir.joinpath(f'{lyr_name}_daily_IITB.csv'))
    print(f'\n{lyr_name} Completed!!!\n')


# ---------------------input-----------------------------------------
out_dir = Path.home().joinpath("Code", "atree", "scripts",
                               "evapotranspiration", "IITB", "output")

IITB_dates = ['20180602', '20180610', '20180618', '20180626', '20180704',
              '20180712', '20180720', '20180728', '20180805', '20180813',
              '20180821', '20180829', '20180906', '20180914', '20180922',
              '20180930', '20181008', '20181016', '20181024', '20181101',
              '20181109', '20181117', '20181125', '20181203', '20181211',
              '20181219', '20181227', '20190101', '20190109',
              '20190117', '20190125', '20190202', '20190210', '20190218',
              '20190226', '20190306', '20190314',
              '20190322', '20190330', '20190407', '20190415', '20190423',
              '20190501', '20190509', '20190517', '20190525'
              ]

i_coll = ee.ImageCollection('users/jaltol/ET_new/IITB')

col_name = 'DISTRICT'  # Unique column heading in Attribute table of shp

start_date = datetime.strptime("20180601", "%Y%m%d")
end_date = datetime.strptime("20190531", "%Y%m%d")
dates_list = [
    (start_date + timedelta(days=x))
    for x in range((end_date - start_date).days + 1)
]
orig_date = datetime.strptime("20180525", "%Y%m%d")

for layer in iface.mapCanvas().layers():
    main(layer)

print('\nAll Completed..............\n')
