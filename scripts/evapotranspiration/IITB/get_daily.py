import json
from qgis.core import QgsJsonExporter
import ee
ee.Initialize()
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

out_dir = Path.home().joinpath("Code","atree","scripts","evapotranspiration","IITB","output")

def get_feature_collection(active_lyr):
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

i_coll = ee.ImageCollection('users/jaltol/ET_new/IITB')
source_lyr = iface.activeLayer()
f_col = get_feature_collection(source_lyr)
f_col_size = f_col.size().getInfo()
f_col_list = f_col.toList(f_col_size)
col_name = 'DISTRICT'


IITB_dates = ['20180602','20180610','20180618','20180626','20180704','20180712',
    '20180720','20180728','20180805','20180813','20180821','20180829','20180906','20180914',
    '20180922','20180930','20181008','20181016','20181024','20181101','20181109',
    '20181117','20181125','20181203','20181211','20181219','20181227','20190101','20190109',
    '20190117','20190125','20190202','20190210','20190218','20190226','20190306','20190314',
    '20190322','20190330','20190407','20190415','20190423','20190501','20190509',
    '20190517','20190525'
]

start_date = datetime.strptime("20180601","%Y%m%d")
end_date = datetime.strptime("20190531","%Y%m%d")
dates_list = [
    (start_date + timedelta(days=x))
    for x in range((end_date - start_date).days + 1)
]
orig_date = datetime.strptime("20180525","%Y%m%d")
print(f'{orig_date:%Y%m%d}')

def get_image(date):
    image = i_coll.filterDate(f'{date:%Y-%m-%d}', f'{(date+timedelta(days=1)):%Y-%m-%d}')
    im_size = image.size().getInfo()
    # print(im_size)
    assert im_size == 1
    return image.first().updateMask(image.first().gte(0))

def calc(feature):
    name = feature.getInfo()['properties'][col_name]
    params = {
        'reducer': ee.Reducer.mean(), 
        'geometry': feature.geometry(),
        'scale': 5000,
        'maxPixels': 1e12
    }
    result = image.reduceRegion(**params).getInfo()
    return name, result

def get_data():
    data_dict = {}
    # for num in range(f_col_size):
        # feature = ee.Feature(f_col_list.get(num))
    with ThreadPoolExecutor() as ex:
        futures = [ex.submit(calc, ee.Feature(f_col_list.get(num))) for num in range(f_col_size)]
    
    for future in as_completed(futures):
        # final.append(future.result())
        name, result = future.result()
        data_dict[name] = result['b1']
    return data_dict

image = get_image(orig_date)
data = get_data()
# print(data)

output_dict = {}
for date in dates_list:
    date_str = f'{date:%Y%m%d}'
    month = date.strftime("%b")
    print(date_str)
    if date_str in IITB_dates:
        image = get_image(date)
        data = get_data()
    output_dict[date_str] = data
    output_dict[date_str].update({'month':month})

# print(output_dict)
df = pd.DataFrame(output_dict).T
df.to_csv(out_dir.joinpath('daily_IITB.csv'))
print('\nCompleted!!!\n')