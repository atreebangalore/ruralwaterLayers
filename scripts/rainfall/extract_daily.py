from pathlib import Path
import pandas as pd
import ee
ee.Initialize()

imd = ee.ImageCollection('users/jaltolwelllabs/IMD/rain')

fc = ee.FeatureCollection('users/balakumaranrm/TCPL/TCPL_Locations')
fc_names = fc.aggregate_array('Name').getInfo()
print(fc_names)

start_date = '2018-01-01'
end_date = '2024-01-01'

im_col = imd.filterDate(start_date, end_date)

def get_stats(image, roi):
    stat = image.reduceRegion(
        geometry=roi.geometry(),
        reducer=ee.Reducer.mean(),
        scale=100,
        crs='EPSG:4326',
    )
    return image.set({'p':stat.get('b1')})

for name in fc_names:
    feat = fc.filter(ee.Filter.eq('Name', name)).first()
    im_proc = im_col.map(lambda x: get_stats(x, feat))
    p_vals = im_proc.aggregate_array('p').getInfo()
    dates = im_proc.aggregate_array('system:index').getInfo()
    out_dict = {'precipitation(mm)': dict(zip(dates, p_vals))}
    out_path = Path(r'C:\Users\atree\Data\imd\rain').joinpath(f'{name}_imd.csv')
    pd.DataFrame(out_dict).to_csv(out_path)

print('completed!!!')