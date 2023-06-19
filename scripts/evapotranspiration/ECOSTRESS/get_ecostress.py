"""Download ECOSTRESS data for given shape file through AppEEARS API.
Recommended that Shape file holds a single feature or by default the first
feature will be selected. Also make sure the feature is of type POLYGON and 
not MULTIPOLYGON, if MULTIPOLYGON extract the POLYGON needed in ArcGIS or QGIS.
[shp file containing one feature which is of POLYGON type mandatory]
Create account in https://appeears.earthdatacloud.nasa.gov/ for username and
password
EarthData or USGS account already registered can be used.

Calculation for Wm-2 to mm:
1 W.m-2 = 0.0864 MJ.m-2.day-1 [ref 1]
1mm of water = 2.45 MJ.m-2 [ref 2]
1 MJ.m-2 = (1 / 2.45) mm
0.0864 MJ.m-2 = (0.0864/2.45) mm
1 W.m-2 = 0.0864 MJ.m-2 = 0.03526 mm of water
Verification [ref 3]

Returns:
    GeoTiff: ECOSTRESS GeoTiff files downloaded and converted to mm
"""
from pathlib import Path
import os
import requests
import sys
import time
import geopandas as gpd
from datetime import datetime, timedelta
import rasterio
from typing import Tuple, Dict

dataFol = Path.home().joinpath("Data","et","ecostress")
dataFol.mkdir(parents=True, exist_ok=True)

def get_coordinates(filepath: str) -> Tuple[Tuple[float,float]]:
    """Get the coordinates of geometry for the feature from shapefile

    Args:
        filepath (str): Path of the shape file

    Returns:
        Tuple[Tuple[float,float]]: Coordinates of geometry
    """
    myshpfile = gpd.read_file(filepath)
    return myshpfile.__geo_interface__["features"][0]["geometry"]["coordinates"][0]

def task_json(coords: Tuple[Tuple[float,float]], start_date_ecostress: str, end_date_ecostress: str, taskname: str):
    return {
            "params": {
                "geo": {
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        coords
                    ]
                    },
                    "properties": {}
                }]
                },
                "dates": [{
                "endDate": end_date_ecostress,
                "startDate": start_date_ecostress
                }],
                "layers": [{
                "layer": "EVAPOTRANSPIRATION_PT_JPL_ETdaily",
                "product": "ECO3ETPTJPL.001"
                }],
                "output": {
                "format": {
                    "type": "geotiff"
                },
                "projection": "geographic"
                }
            },
            "task_name": taskname,
            "task_type": "area"
            }

def create_task(task: Dict[str,Dict[str,str]], token: str) -> str:
    """Create the Task in AppEEARS

    Args:
        task (Dict[str,Dict[str,str]]): Task input JSON
        token (str): AppEEARS token

    Returns:
        str: Task id
    """
    response_eco = requests.post(
        'https://appeears.earthdatacloud.nasa.gov/api/task',
        json=task,  
        headers={'Authorization': 'Bearer {0}'.format(token)})
    task_response_eco = response_eco.json()
    return task_response_eco['task_id']

def check_status(task_id: str, token: str) -> bool:
    """Get the status of Task in AppEEARS

    Args:
        task_id (str): Task id
        token (str): AppEEARS token

    Returns:
        bool: True or False of whether Task is not completed
    """
    response = requests.get(
        'https://appeears.earthdatacloud.nasa.gov/api/status/{0}'.format(task_id), 
        headers={'Authorization': 'Bearer {0}'.format(token)})
    status_response = response.json()
    try:
        status = status_response['status']
    except KeyError:
        status = 'processing'
    print(f'status of task is: {status}')
    return status != 'done'

def progress(task_id: str, token: str):
    """Check the progress of Task every 60 seconds until done

    Args:
        task_id (str): Task id for task in AppEEARS
        token (str): AppEEARS token
    """
    not_completed = True
    count = 0
    while not_completed:
        not_completed = check_status(task_id, token)
        if not_completed:
            print(f"checking status again in 60 seconds... {count}")
            count += 1
            time.sleep(60)

def get_token(username: str, password: str) -> str:
    """generate token from the AppEEARS

    Args:
        username (str): AppEEARS username
        password (str): AppEEARS password

    Returns:
        str: AppEEARS Token
    """
    response_eco = requests.post(
        'https://appeears.earthdatacloud.nasa.gov/api/login',
        auth=(username, password))
    token_response_eco = response_eco.json()
    print(f'AppEEARS Token: {token_response_eco["token"]}')
    print(f'AppEEARS Token expiration: {token_response_eco["expiration"]}')
    return token_response_eco['token']

def download_data(task_id: str, token: str, dpath: Path):
    """Get file details from API, Download and Store the GeoTiff files

    Args:
        task_id (str): Task id
        token (str): Token from the AppEEARS API
        dpath (Path): Path to store the downloaded files
    """
    response_eco_bundle = requests.get(
        'https://appeears.earthdatacloud.nasa.gov/api/bundle/{0}'.format(task_id),  
        headers={'Authorization': 'Bearer {0}'.format(token)}
    )
    bundle_response = response_eco_bundle.json()
    files_num = len(bundle_response['files'])
    print(f'Total Number of Files: {files_num}')
    for i in range(files_num):
        response = requests.get(
            'https://appeears.earthdatacloud.nasa.gov/api/bundle/{0}/{1}'.format(task_id, bundle_response['files'][i]['file_id']),
            headers={'Authorization': 'Bearer {0}'.format(token)}, 
            allow_redirects=True,
            stream=True)
        with open(os.path.join(dpath, os.path.split(bundle_response['files'][i]['file_name'])[-1]), 'wb') as f:
            for data in response.iter_content(chunk_size=8192):
                f.write(data)
        print(f'Downloaded Files: {i+1}/{files_num}')

def dpipeline(download_path: Path, start_date_ecostress: str, end_date_ecostress: str, task_name: str, shp_path: str, username: str, password: str):
    """Pipeline for downloading ECOSTRESS data through AppEEARS API.

    Args:
        download_path (Path): Path to download the files
        start_date_ecostress (str): Start Date
        end_date_ecostress (str): End Date
        task_name (str): Task Name
        shp_path (str): Path to the shapefile
        username (str): AppEEARS username
        password (str): AppEEARS password
    """
    token_eco = get_token(username, password)
    print('Reading shape file and getting coordinates of the feature')
    coords = get_coordinates(shp_path)
    print('Creating Task!!!')
    task = task_json(coords, start_date_ecostress, end_date_ecostress, task_name)
    task_id = create_task(task, token_eco)
    print(f'Task id: {task_id}')
    progress(task_id, token_eco)
    time.sleep(5)
    download_data(task_id, token_eco, download_path)
    print(f'Download Location: {download_path}')

def get_date(file: str) -> Tuple[str, str]:
    """Get the Calendar date from Julian date

    Args:
        file (str): downloaded filename

    Returns:
        Tuple[str,str]: date in calendar format and Time
    """
    doy = file.split('_')[-2]
    year = doy[3:7]
    doy_int = int(doy[7:10])-1
    time = doy[10:16]
    start = datetime.strptime(f'{year}-01-01', '%Y-%m-%d')
    end = datetime.strptime(f'{year}-12-31', '%Y-%m-%d')
    year_list = [start.strftime('%Y%m%d')]
    while start != end:
        start+=timedelta(days=1)
        year_list.append(start.strftime('%Y%m%d'))
    return year_list[doy_int], time

def unit_conversion(input: Path, output: Path):
    """Conversion of Wm-2 to mm

    Args:
        input (Path): Path of input file
        output (Path): Path of output file
    """
    with rasterio.open(input, 'r') as dataset:
        image = dataset.read(1)
        out_meta = dataset.meta
    image = image * 0.03526 # Wm-2 to mm conversion
    with rasterio.open(output, "w", **out_meta) as dest:
        dest.write(image,1)

def cpipeline(d_path: Path, c_path: Path):
    """Pipeline for conversion of Wm-2 to mm

    Args:
        d_path (Path): Path where downloaded files are located
        c_path (Path): Path where converted files to store
    """
    print('Converting Files... Wm-2 to mm units')
    files = [
        file
        for file in os.listdir(d_path)
        if os.path.splitext(file)[1] == '.tif'
    ]
    for file in files:
        print(f'converting: {file}')
        date, time = get_date(file)
        print(f'Julian date converted: {date} & {time}')
        in_path = d_path.joinpath(file)
        outname = f'ECO3ETPTJPL.001_EVAPOTRANSPIRATION_PT_JPL_ETdaily_{date}_{time}.tif'
        out_path = c_path.joinpath(outname)
        unit_conversion(in_path, out_path)
        print(f'converted: {outname}')

def main(shp_path:str, start:str, end:str, username:str, password:str):
    """
    Download ECOSTRESS data for given shape file through AppEEARS API.
    Recommended that Shape file holds a single feature or by default the first
    feature will be selected. type accepted is POLYGON, not MULTIPOLYGON.
    Please avoid special characters in the Password.
    
    args:
        shp_path(str): path of the shape file
        start(str): start date (YYYYMMDD)
        end(str): end date (YYYYMMDD)
        username(str): username for AppEEARS
        password(str): password for AppEEARS
    
    example:
    python Code/atree/scripts/evapotranspiration/ECOSTRESS/get_ecostress.py C:/ECOSTRESS/shp/Raichur.shp 20200101 20201231 username password
    
    output:
    the converted tif files are saved at {Home Dir}/Data/et/ecostress/
    """
    filename = os.path.basename(shp_path).split('.')[0]
    task_name = f'{filename[:10]}-{start}-{end}'
    print(f'Task: {task_name}')
    try:
        start_date = datetime.strptime(start, '%Y%m%d')
        end_date = datetime.strptime(end, '%Y%m%d')
        start_date_ecostress = start_date.strftime('%m-%d-%Y')
        end_date_ecostress = end_date.strftime('%m-%d-%Y')
    except ValueError as e:
        print('Check the dates....\n', e)
        sys.exit()
    dest_dir = dataFol.joinpath(task_name)
    dest_dir.mkdir(parents=True, exist_ok=True)
    download_path = dest_dir.joinpath('downloaded')
    try:
        download_path.mkdir(parents=True)
        dpipeline(download_path, start_date_ecostress, end_date_ecostress, task_name, shp_path, username, password)
    except KeyError as exc:
        raise TypeError('Strip shapefile from MULTIPOLYGON to POLYGON') from exc
    except Exception:
        print(f'Task "{task_name}" already downloaded at \n{download_path}')
    convert_path = dest_dir.joinpath('converted')
    try:
        convert_path.mkdir(parents=True)
        cpipeline(download_path, convert_path)
        print(f'output files at {convert_path}')
    except Exception:
        print(f'Task "{task_name}" already converted at \n{convert_path}')

if __name__=='__main__':
    shp_path = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]
    username = sys.argv[4]
    password = sys.argv[5]
    main(shp_path, start, end, username, password)

'''
References:

1. https://www.fao.org/3/X0490E/x0490e0i.htm#:~:text=1%20W%20m%2D2%20%3D%200.0864%20MJ%20m%2D2%20day%2D1
2. ECOSTRESS Documentation "Level-3 Evapotranspiration L3(ET_PT-JPL) Algorithm Theoretical Basis Document"
3. https://www.researchgate.net/post/How_to_convert_30minute_evapotranspiration_in_watts_to_millimeters#:~:text=1%20MJ%20%2Fm2%2Fday%20%3D0.408%20mm%20%2Fday%20
'''