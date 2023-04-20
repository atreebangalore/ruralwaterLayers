from pathlib import Path
import os
import requests
import sys
import time
import geopandas as gpd
from datetime import datetime, timedelta

dataFol = Path.home().joinpath("Data","et","ecostress")
dataFol.mkdir(parents=True, exist_ok=True)

def get_coordinates(filepath):
    myshpfile = gpd.read_file(filepath)
    return myshpfile.__geo_interface__["features"][0]["geometry"]["coordinates"][0]

def task_json(coords,start_date_ecostress,end_date_ecostress,taskname):
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

def create_task(task, token):
    response_eco = requests.post(
        'https://appeears.earthdatacloud.nasa.gov/api/task',
        json=task,  
        headers={'Authorization': 'Bearer {0}'.format(token)})
    task_response_eco = response_eco.json()
    return task_response_eco['task_id']

def check_status(task_id, token):
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

def progress(task_id, token):
    not_completed = True
    count = 0
    while not_completed:
        not_completed = check_status(task_id, token)
        if not_completed:
            print(f"checking status again in 60 seconds... {count}")
            count += 1
            time.sleep(60)

def get_token(username, password):
    response_eco = requests.post(
        'https://appeears.earthdatacloud.nasa.gov/api/login',
        auth=(username, password))
    token_response_eco = response_eco.json()
    print(f'AppEEARS Token: {token_response_eco["token"]}')
    print(f'AppEEARS Token expiration: {token_response_eco["expiration"]}')
    return token_response_eco['token']

def download_data(task_id, token, dpath):
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

def dpipeline(download_path, start_date_ecostress, end_date_ecostress, task_name, shp_path, username, password):
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

def get_date(file: str):
    doy = file.split('_')[-2]
    year = doy[3:7]
    doy = int(doy[7:10])-1
    start = datetime.strptime(f'{year}-01-01', '%Y-%m-%d')
    end = datetime.strptime(f'{year}-12-31', '%Y-%m-%d')
    year_list = [start.strftime('%Y%m%d')]
    while start != end:
        start+=timedelta(days=1)
        year_list.append(start.strftime('%Y%m%d'))
    return year_list[doy]

def cpipeline(d_path):
    print('Converting Files....')
    files = [
        file
        for file in os.listdir(d_path)
        if os.path.splitext(file)[1] == '.tif'
    ]
    for file in files:
        date = get_date(file)
        filename = f'ECO3ETPTJPL.001_EVAPOTRANSPIRATION_PT_JPL_ETdaily_{date}.tif'

def main(shp_path:str, start:str, end:str, username:str, password:str):
    """
    args:
        shp_path(str): path of the shape file
        start(YYYYMMDD): start date
        end(YYYYMMDD): end date
        username(str): username for AppEEARS
        password(str): password for AppEEARS
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
    except Exception:
        print(f'Task "{task_name}" already downloaded at \n{download_path}')
    convert_path = dest_dir.joinpath('converted')
    try:
        convert_path.mkdir(parents=True, exist_ok=True) # remove exits_ok after completion
        cpipeline(download_path)
    except Exception:
        print(f'Task "{task_name}" already converted at \n{convert_path}')

if __name__=='__main__':
    shp_path = sys.argv[1]
    start = sys.argv[2]
    end = sys.argv[3]
    username = sys.argv[4]
    password = sys.argv[5]
    main(shp_path, start, end, username, password)