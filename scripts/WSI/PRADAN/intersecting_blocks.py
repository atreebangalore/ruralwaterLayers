import ee
import pandas as pd
from pathlib import Path

ee.Initialize()

unique_field = 'village_na'
buffer_distance = 5000  # 5 kilometers
statReducer = 'stdDev' # 'median' or 'stdDev'

feature_collection = ee.FeatureCollection('users/balakumaranrm/PRADAN/villages_CH_WB')
shrug = ee.FeatureCollection('users/balakumaranrm/PRADAN/SHRUG_CH_WB')
srtm = ee.Image('USGS/SRTMGL1_003').select('elevation')
srtm_slope = ee.Terrain.slope(srtm)

dataFol = Path(r'C:\Users\atree\Data\slope')
dataFol.mkdir(parents=True, exist_ok=True)
vectorFol = dataFol.joinpath('villages')
vectorFol.mkdir(parents=True, exist_ok=True)

def median_slope(fc, image):
    return image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.median(),
        scale=30,
        crs="EPSG:4326",
    ).getInfo()

def stdDev_slope(fc, image):
    return image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.stdDev(),
        scale=30,
        crs="EPSG:4326",
    ).getInfo()

def get_slope(fc, image):
    if statReducer == 'stdDev':
        stats = stdDev_slope(fc, image)
    elif statReducer == 'median':
        stats = median_slope(fc, image)
    else:
        raise AttributeError('statReducer mentioned not correct')
    out_dict = {}
    for feat in stats['features']:
        props = feat['properties']
        # print(props)
        name = props[unique_field]
        value = props[statReducer]
        out_dict[name]=value
    return out_dict

def buffer_and_intersect(feature):
    buffered_feature = feature.geometry().buffer(buffer_distance)

    filtered = shrug.filterBounds(buffered_feature).aggregate_array(unique_field)
    
    return feature.set('intersects', filtered)

def intersecting(fc, selected_list):
    intersecting_features_collection = fc.map(buffer_and_intersect)
    result = intersecting_features_collection.getInfo()
    out_dict = {}
    for feat in result['features']:
        props = feat['properties']
        # print(props)
        name = props[unique_field]
        # print(name)
        intersects = props['intersects']
        # print(intersects)
        for vname in selected_list:
            if vname in intersects:
                intersects.remove(vname)
        out_dict[name]=intersects
    return out_dict

def main():
    print('started!!!')
    fc_dict = feature_collection.getInfo()
    selected_list = [feat['properties'][unique_field] for feat in fc_dict['features']]
    int_dict = intersecting(feature_collection, selected_list)
    # print(int_dict)
    selected_buffer = feature_collection.geometry().buffer(buffer_distance+1000)
    slope_dict = get_slope(shrug.filterBounds(selected_buffer), srtm_slope)
    # print(slope_dict)
    final_dict = {}
    for filename, int_villages in int_dict.items():
        filepath = dataFol.joinpath('villages', f'{filename}_{statReducer}_slope.csv')
        out_dict = {
            village: {
                filename: slope_dict[filename],
                f'{statReducer}_slope': slope_dict[village],
                'abs_perc_diff': abs(
                    (
                        (slope_dict[village] - slope_dict[filename])
                        / slope_dict[filename]
                    )
                    * 100
                ),
            }
            for village in int_villages
        }
        df = pd.DataFrame(out_dict).T
        # print(df)
        df.to_csv(filepath)
        if df.shape[0]:
            sorted_vals = sorted(df['abs_perc_diff'].values)
            final_dict[filename] = {
                    'village1': df.index[df['abs_perc_diff']==sorted_vals[0]].to_list()[0],
                    'village2': df.index[df['abs_perc_diff']==sorted_vals[1]].to_list()[0] if len(sorted_vals)>1 else 0,
                }
    # print(final_dict)
    final_df = pd.DataFrame(final_dict).T
    finalpath = dataFol.joinpath(f'similar_villages_{statReducer}_slope.csv')
    # print(final_df)
    final_df.to_csv(finalpath)
    print('completed!!!')

main()