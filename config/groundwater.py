from pathlib import Path
import inspect

rootFol = Path.cwd()

def get_params(states_str,dataset='consolidated'):
    stack = inspect.stack()
    frm = inspect.stack()[1]
    step = frm[1].split(".")[0].split("_")[2].lower()
    print(step)

    if step=="preprocess":        
        path = rootFol.joinpath("data","groundwater","cgwb_stationwise_historical","CGWB_original.csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    elif step=="elevations":
        path = rootFol.joinpath("outputs","groundwater","levels","preprocessed",states_str+"_processed.csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    elif step=="rechargedischarge":
        path = rootFol.joinpath("outputs","groundwater","levels","preprocessed",states_str+"_processed.csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    elif step=="rasterize":
        path = rootFol.joinpath("outputs","groundwater","levels","preprocessed",states_str+"_processed.csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    else:
        raise Exception("dataset must be either 'preprocess' or 'elevations'")
    return (path,metacols)


def grid_params(gridalg):
    if gridalg =="gdal:gridinversedistance":
        return {
        'POWER':2,    # FOR gridinversedistance
#         'RADIUS':0.25,    # FOR gridinversedistancenearestneighbor / gridlinear
#         'RADIUS_1':0.25,    # FOR gridinversedistance / gridnearestneighbor / gridaverage
#         'RADIUS_2':0.25,    # FOR gridinversedistance  /  gridnearestneighbor / gridaverage
        'MAX_POINTS':12,    # FOR gridinversedistance 
        'MIN_POINTS':1,    # FOR gridinversedistance / gridaverage
        'NODATA': -9999,
    }