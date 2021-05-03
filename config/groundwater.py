from pathlib import Path
import inspect

rootFol = Path.cwd()

def get_params(state,dataset='consolidated'):
    stack = inspect.stack()
    frm = inspect.stack()[1]
    step = frm[1].split(".")[0].split("_")[1].lower()

    if step=="preprocess":        
        path = rootFol.joinpath("data","groundwater","cgwb_stationwise_historical","CGWB_original.csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    elif step=="elevations":
        path = rootFol.joinpath("outputs","groundwater","csv",state+"_processed.csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    elif step=="rechargedischarge":
        path = rootFol.joinpath("outputs","groundwater","csv",state+"_processed_wElev.csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    elif step=="rasterize":
        path = rootFol.joinpath("outputs","groundwater","csv",state+"_processed_wRD.csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    else:
        raise Exception("dataset must be either 'preprocess' or 'elevations'")
    return (path,metacols)

#     elif dataset=="monthly":
#         cgwbStnFol = dataFol.joinpath("groundwater","cgwb_stationwise_wloc")
#         path = cgwbStnFol.joinpath("groundwater_StateWiseStationLevelReport_Karnataka_monthly_052020_102020.xls")
#         metacols = ["STATE","DISTRICT","STATION","Latitude","Longtitude","Station Type"]
#     elif dataset=="consolidated_processed":
#         path = rootFol.joinpath("outputs","final","csv",state+"_processed_w"+param+".csv")
#         metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]