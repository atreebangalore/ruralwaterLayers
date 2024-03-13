import ee
import pandas as pd
from pathlib import Path

ee.Initialize()

buffer_distance = 10000  # 10 kilometers

feature_collection = ee.FeatureCollection('users/balakumaranrm/PRADAN/WB_Sampled_Blocks')
srtm = ee.Image('USGS/SRTMGL1_003').select('elevation')
srtm_slope = ee.Terrain.slope(srtm)

dataFol = Path(r'C:\Users\atree\Data\slope')

def median_slope(fc, image):
    return image.reduceRegions(
        collection=fc,
        reducer=ee.Reducer.median(),
        scale=30,
        crs="EPSG:4326",
    ).getInfo()

def get_slope(fc, image):
    stats = median_slope(fc, image)
    out_dict = {}
    for feat in stats['features']:
        props = feat['properties']
        name = props['sd_name']
        value = props['median']
        out_dict[name]=value
    return out_dict

def buffer_and_intersect(feature):
    buffered_feature = feature.geometry().buffer(buffer_distance)

    filtered = feature_collection.filterBounds(buffered_feature).aggregate_array('sd_name')
    
    return feature.set('intersects', filtered)

def intersecting(fc):
    intersecting_features_collection = fc.map(buffer_and_intersect)
    result = intersecting_features_collection.getInfo()
    out_dict = {}
    for feat in result['features']:
        props = feat['properties']
        name = props['sd_name']
        intersects = props['intersects']
        intersects.remove(name)
        out_dict[name]=intersects
    return out_dict

def main():
    print('started!!!')
    int_dict = intersecting(feature_collection)
    # print(int_dict)
    slope_dict = get_slope(feature_collection, srtm_slope)
    # print(slope_dict)
    final_dict = {}
    for filename, int_villages in int_dict.items():
        filepath = dataFol.joinpath('villages', f'{filename}_median_slope.csv')
        out_dict = {
            village: {
                filename: slope_dict[filename],
                'median_slope': slope_dict[village],
                'abs_perc_diff': abs(round(
                    (
                        (slope_dict[village] - slope_dict[filename])
                        / slope_dict[filename]
                    )
                    * 100,
                    2,
                )),
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
    finalpath = dataFol.joinpath('similar_villages_median_slope.csv')
    # print(final_df)
    final_df.to_csv(finalpath)
    print('completed!!!')

main()