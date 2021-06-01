this repo contains scripts to import and/or pre-process the layers required for the Rural Water Security Plugin <br>
below are a few examples showing how to run these scripts yourself <br>

# Groundwater

## Groundwater levels
---
### Original dataset
CSV : data\groundwater\cgwb_stationwise_historical\CGWB_original.csv
Columns: STATE, DISTRICT, LAT, LON, SITE_TYPE, WLCODE, May-96, Aug-96, Nov-96, Jan-97,... Nov-16, Jan-17 <br>
  Dataset contains 28k+ well locations in India, with their historical water levels (BGL) in May, Aug, Nov, Jan.
  
### Preprocessed dataset
i/p: takes original dataset as input <br>
processing: preprocessing involves subsetting by State , removing nulls, duplicates
    and duplicate geometries, then saving to CSV, SHP (with data) and SHP (geoms only) <br>
Typical usage (in terminal from root directory): <br>
$ python layers/groundwater/levels/gw_preProcess.py [ST]   # [ST] is two letter short code for state name <br>
o/p: outputs/groundwater/csv/[ST]_metadata.log, <br> 
outputs/groundwater/csv/[ST]_processed.csv <br>
outputs/groundwater/shapefiles/[ST]_processed.shp <br>

### Elevations dataset
i/p: takes preprocessed dataset as input <br>
processing: reads in a pre-processed groundwater layer (SHP) and returns elevations, depth-to-water (above MSL) for each <br>
Typical usage (in terminal from root directory): <br>
$ python layers/groundwater/levels/gw_elevations.py [ST] <br>
o/p: outputs/groundwater/csv/[ST]_metadata.log, <br> 
outputs/groundwater/csv/[ST]_processed_wElev.csv <br>
outputs/groundwater/shapefiles/[ST]_processed_wElev.shp <br>

### Recharge-Discharge
i/p: takes dataset with elevations as input <br>
processing: reads in a pre-processed groundwater layer with depth to water (above MSL) (CSV) and returns monsoon recharge, non-monsoon discharge for all years <br>
Typical usage (in terminal from root directory): <br>
$ python layers/groundwater/levels/gw_RechargeDischarge.py [ST]  <br>
o/p: outputs/groundwater/csv/[ST]_metadata.log, <br> 
outputs/groundwater/csv/[ST]_processed_wRD.csv <br>
outputs/groundwater/shapefiles/[ST]_processed_wRD.shp <br>

### Rasterize
i/p: takes dataset with recharge-discharge as input <br>
processing: reads in a pre-processed groundwater layer, with recharge-discharge (CSV) and returns tif <br>
Typical usage (in terminal from root directory): <br>
$ python layers/groundwater/levels/gw_Rasterize.py [ST] <br>
o/p: outputs/groundwater/csv/[ST]_metadata.log, <br> 
outputs/groundwater/csv/[ST]_processed_wRD.csv <br>
outputs/groundwater/shapefiles/[ST]_processed_wRD.shp <br>


## Geology
---
To be completed


# Evapotranspiration
---
### Import
Source: [monthly ET](https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/eta/downloads/) , [yearly ET](https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/yearly/eta/downloads/)
requires command line tool 'wget' to be installed'
download these as needed with `wget -i layers/evapotranspiration/listoflinks.txt`

### Clip to India
use gdal batch script in layers/evapotranspiration/


# Rainfall
---
Source: [historical rainfall](https://imdpune.gov.in/Clim_Pred_LRF_New/Grided_Data_Download.html)


