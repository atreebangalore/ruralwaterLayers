# Rural Water Layers - Jaltol - Scripts

This repo contains scripts to import and/or pre-process the layers required for the Rural Water Security Plugin.

## Initial Setup
Install miniconda and create a virutal environment for python3.7

refer [Conda Cheat Sheet](https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf)

> The Home Directory for different OS,
>
> windows: C:\Users\USERNAME
>
> mac: /Users/USERNAME
>
> linux: /home/USERNAME

create directory named 'Code' and 'Data' in Home Directory
```
mkdir Code
```

clone this repository inside 'Code' dir
```
cd Code
git clone https://github.com/atreebangalore/ruralwaterLayers.git
```

rename 'ruralwaterLayers' into 'atree'
```
mv ruralwaterLayers atree
```

Install the required packages in the python environment.
```
pip install -r requirements.txt
```

### Usage

in general, execute the scripts from the home directory,
```
python Code/atree/scripts/{dataLayer}/{script}.py [arguments]
```
arguments may vary based on the script.

# Equity
Calculation of Gini coefficient of Evapotranspiration vales for districts of the chosen states.
### Usage
```
python Code/atree/scripts/equity/1_getETValues.py [Year] [ST]
python Code/atree/scripts/equity/2_calcGiniValues.py [Year] [ST]
```
Equity has two script to be executed successively.

They both take two arguments,

### Args:

Year - interger value for the water year. (YYYY)

ST - Two letter Abbreviated State Names seperated by comma.

### Example
```
python Code/atree/scripts/equity/1_getETValues.py 2018 KA,TN
python Code/atree/scripts/equity/2_calcGiniValues.py 2018 KA,TN
```
### Output
The corresponding output csv files will be saved in the path `Code/atree/outputs/equity`

# Evapotranspiration
Downloads monthly SEBOP ET images and generation of yearly SEBOP ET image by summation of the monthly images and extraction of ET pixel values for districts of chosen state.

Requires the shape file of SOI National Boundary to be located at `{Home Dir}\Data\gis\soi_national_boundary.shp`

*getWaterYrSEBOP.py will call getMonthlySEBOP.py script to download monthly images.*
### Usage
```
python Code/atree/scripts/evapotranspiration/getWaterYrSEBOP.py [Year]
```
### Args:

Year - integer value for the water year 

### Example
```
python Code/atree/scripts/evapotranspiration/getWaterYrSEBOP.py 2019
```
### Output
Monthly SEBOP images will be downloaded to `{Home Dir}/Data/et/sebop/`

also in that same loaction annual year SEBOP ET image will be generated as `wy{year}_india.tif`.

## getMonthlySEBOP.py & clipMonthlySEBOP.py
Downloads ET zip data from [USGS](https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/eta/downloads/) for specified month and year. Extract the zip file and clip it to the soi_national_boundary.shp extent.

To download SEBOP data, wget utility is required.

windows - place the [wget.exe](https://eternallybored.org/misc/wget/) file in the location C:\Windows\System32

mac & linux - prebuilt into the OS.
### Usage:
```
python Code/atree/scripts/evapotranspiration/getMonthlySEBOP.py [Year] [Month]
python Code/atree/scripts/evapotranspiration/clipMonthlySEBOP.py [Year] [Month]
```
### Args
Year - Year for which data is to be downloaded

Month - two digit month for which data to be downloaded (eg: 04)

## SSEBopMonthlyGCP2GEE.py
upload the ET SSEBop files from GCP bucket to the GEE Image Collection
### Usage
```
python Code/atree/scripts/rainfall/IMDHistoricalGCP2GEE.py [year] [bucket] [user] [coll]
```
### Args
year - monthly images of the year to upload

bucket - Google Cloud Platform bucket name

user - Google Earth Engine Username

coll - Google Earth Engine Image Collection name

## fao/pAnnualDaytimeHrs.py
MEAN DAILY PERCENTAGE (p) OF ANNUAL DAYTIME HOURS FOR DIFFERENT LATITUDES
calculated by [FAO](https://www.fao.org/3/s2022e/s2022e07.htm#3.1.3%20blaney%20criddle%20method) method

Requires a tmax or tmin tif file from IMDHistoricalTif2Daily output as a reference to generate the skeleton of p value tif file.
### Usage:
```
python Code\atree\scripts\evapotranspiration\fao\pAnnualDaytimeHrs.py [var_type] [filename]
```
### Args:
var_type: tmax or tmin 

filename: filename of output from IMDHistoricalTif2Daily.py for tmax or tmin
### Output:
{Home Dir}\Data\et\fao\p_value\

## fao/refCropET.py
Calculate Reference Crop ET as per [FAO](https://www.fao.org/3/s2022e/s2022e07.htm#3.1.3%20blaney%20criddle%20method), This script requires p-value from pAnnualDaytimeHrs.py and mean Temperature from IMDHistoricalMeanTemp.py which in-turn requires max and min IMD Temperature Imagery.
### Usage:
```
python Code/atree/scripts/evapotranspiration/fao/refCropET.py [start_yr] [end_yr]
```
### Args:
start_yr : Starting year

end_yr : Ending year
### Output:
{Home Dir}/Data/et/fao/refCropET/{year}

## getDistrictValues.py 
```
python Code/atree/scripts/evapotranspiration/getDistrictValues.py [StateName] [Year]
```
### Args:

StateName - state name as in {StateName}_district_boundary.shp

Year - integer value for the water year (year for which monthly images were downloaded).

Requires district shape file of chosen state to be loacated at `{Home Dir}\Data\gis\{State Name}_district_boundary.shp`

### Example
```
python Code/atree/scripts/evapotranspiration/getDistrictValues.py tamilnadu 2019
```
### Output
csv files for all the districts of chosen state will be generated at `Code/data/evapotranspiration/SEBOP/yearly/stats`

# Rainfall
Downloads IMD gridded data for precipitation or min temp or max temp (IMDHistoricalGrid.py), converts the grd data into annual tif imagery (IMDHistoricalGrid2Tif.py) and splits the annual imagery bands into individual daily imagery (IMDHistoricalTif2Daily.py).
Upload of daily imagery to GEE can be done using IMDHistoricalGCP2GEE.py script.
Summation of Daily imagery into "yearly" or "monthly" or "water yr" (IMDHistoricalDailySum.py).

Calculate monthly Effective Precipitation (effPrecipitation.py) from the 
Daily rainfall images of IMDHistoricalTif2Daily.py

Calculate mean Temperature (IMDHistoricalMeanTemp.py) both daily and monthly
from the Daily max and min Temp images of IMDHistoricalTif2Daily.py

### Usage
```
python Code/atree/scripts/rainfall/IMDHistoricalGrid.py [type] [start_yr] [end_yr]
python Code/atree/scripts/rainfall/IMDHistoricalGrid2Tif.py [type] [start_yr] [end_yr]
python Code/atree/scripts/rainfall/IMDHistoricalTif2Daily.py [type] [start_yr] [end_yr]
python Code/atree/scripts/rainfall/IMDHistoricalGCP2GEE.py [year] [bucket] [user] [coll]
python Code/atree/scripts/rainfall/IMDHistoricalDailySum.py [type] [start_yr] [end_yr] [period]
python Code/atree/scripts/rainfall/effPrecipitation.py [start_yr] [end_yr]
python Code/atree/scripts/rainfall/IMDHistoricalMeanTemp.py [start_yr] [end_yr]
```
### Args:
type - rain or tmin or tmax

start_yr - starting year (YYYY)

end_yr - ending year (YYYY)

year - daily images of the year to upload

bucket - Google Cloud Platform bucket name

user - Google Earth Engine Username

coll - Google Earth Engine Image Collection name

period - annual or monthly or wateryr 
(wateryr is from june 1st of start_yr to may 31st of end_yr)

### Example
```
python Code/atree/scripts/rainfall/IMDHistoricalGrid.py rain 2018 2019
python Code/atree/scripts/rainfall/IMDHistoricalGrid2Tif.py rain 2018 2019
python Code/atree/scripts/rainfall/IMDHistoricalTif2Daily.py rain 2018 2019
python Code/atree/scripts/rainfall/IMDHistoricalDailySum.py rain 2018 2019 wateryr
python Code/atree/scripts/rainfall/effPrecipitation.py 2018 2019
python Code/atree/scripts/rainfall/IMDHistoricalMeanTemp.py 2018 2019
```
### Output
IMDHistoricalGrid.py - Gridded data stored in `{Home Dir}/Data/imd`

IMDHistoricalGrid2Tif.py - `{Home Dir}/Data/imd` (respective folders for grd and tif)

IMDHistoricalTif2Daily.py - `{Home Dir}/Data/imd/rain/tif/{year}/YYYYMMDD.tif`

IMDHistoricalGCP2GEE.py - daily images uploaded to GEE Assets - Image Collection

IMDHistoricalDailySum.py - `{Home Dir}/Data/imd/{type}/tif/period`

effPrecipitation.py - `{Home Dir}/Data/imd/{var_type}/tif/eff_precipitation/monthly`

IMDHistoricalMeanTemp.py - `{Home Dir}/Data/imd/tmean`

# Groundwater
## levels

### Usage
```
python Code/atree/scripts/groundwater/levels/1_gw_preProcess.py [ST]
python Code/atree/scripts/groundwater/levels/2_gw_elevations.py [ST]
python Code/atree/scripts/groundwater/levels/3_gw_rechargedischarge.py [ST]
```
### Args
ST - two letter abbreviated State names seperated by comma.
### Example
```
python Code/atree/scripts/groundwater/levels/1_gw_preProcess.py KA,MH
python Code/atree/scripts/groundwater/levels/2_gw_elevations.py KA,MH
python Code/atree/scripts/groundwater/levels/3_gw_rechargedischarge.py KA,MH
```
### output
csv and shape files at
`{Home Dir}/Code/atree/outputs/groundwater/levels/preprocessed/`

# Surface Water
From the JRC Global Surface Water dataset calculate the Volume of surface water (PreMonsoon and PostMonsoon) as Raster image.

### Usage
```
python Code/atree/scripts/surfaceWater/JRCgetSW.py [year] [ST]
```

### Args
year - year for which the Volume calculation to be made

ST - Two letter abbreviated State Name.

### Example
```
python Code/atree/scripts/surfaceWater/JRCgetSW.py 2019 KA
```

### Output
PreMonsoon and PostMonsoon - two raster images are exported to GDrive.

---
# Old README Content
this repo contains scripts to import and/or pre-process the layers required for the Rural Water Security Plugin <br>
below are a few examples showing how to run these scripts yourself <br>

# Groundwater

## Groundwater levels

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
To be completed


# Evapotranspiration

### Import
Source: [monthly ET](https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/monthly/eta/downloads/) , [yearly ET](https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/fews/web/global/yearly/eta/downloads/)
requires command line tool 'wget' to be installed'
download these as needed with `wget -i layers/evapotranspiration/listoflinks.txt`

### Clip to India
use gdal batch script in layers/evapotranspiration/


# Rainfall

Source: [historical rainfall](https://imdpune.gov.in/Clim_Pred_LRF_New/Grided_Data_Download.html)


