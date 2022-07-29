from pathlib import Path
import inspect

rootFol = Path.home()

def get_params(states_str):
    frm = inspect.stack()[1]
    step = frm[1].split(".")[0].split("_")[2].lower()
    print(step)

    if step=="preprocess":
        # path = rootFol.joinpath("Code","atree","data","groundwater",
                            # "cgwb_stationwise_historical","CGWB_original.csv")
        # metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
        path = rootFol.joinpath("Code","atree","data","groundwater","levels",
                                "level1","CGWB_levels_level1.csv")
        metacols = ['STATE', 'DISTRICT', 'STATION', 'LAT', 'LON', 'Station Type']
    elif step in ["elevations", "rechargedischarge", "rasterize"]:
        # path = rootFol.joinpath("Code", "atree", "outputs", "groundwater", "levels",
        #                        "preprocessed", f"{states_str}_processed.csv")
        # metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
        path = rootFol.joinpath("Code","atree","data","groundwater","levels",
                                "level2",f"{states_str}_processed.csv")
        metacols = ['STATE', 'DISTRICT', 'STATION', 'LAT', 'LON', 'Station Type']
    else:
        raise ValueError("dataset must be either 'preprocess' or 'elevations'")
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