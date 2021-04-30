import os

rootFol = os.getcwd()
                       
def get_params(dataset,state,param=None):
    if dataset=="consolidated":        
        path = os.path.join(rootFol,"data","groundwater","cgwb_stationwise_historical","CGWB_data_wide.csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    elif dataset=="monthly":
        cgwbStnFol = os.path.join(dataFol,"groundwater","cgwb_stationwise_wloc")
        path = os.path.join(cgwbStnFol,"groundwater_StateWiseStationLevelReport_Karnataka_monthly_052020_102020.xls")
        metacols = ["STATE","DISTRICT","STATION","Latitude","Longtitude","Station Type"]
    elif dataset=="consolidated_processed":
        path = os.path.join(rootFol,"outputs","final","csv",state+"_processed_w"+param+".csv")
        metacols = ["SNO","STATE","DISTRICT","SITE_TYPE","WLCODE","LON","LAT"]
    else:
        raise Exception("dataset must be either 'consolidated' or 'monthly'")
    return (path,metacols)