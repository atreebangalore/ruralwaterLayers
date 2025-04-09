# pip install aiohttp
import aiohttp
import asyncio
import requests
import time
import json
from urllib.parse import urlencode
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from math import radians, sin, cos, sqrt, atan2
import ee
ee.Initialize()

station_url = 'https://arc.indiawris.gov.in/server/rest/services/NWIC/GroundwaterLevel_Stations/MapServer/0/query'
data_url = 'https://indiawris.gov.in/gwldnlddata'
requests.packages.urllib3.disable_warnings()  # Disable InsecureRequestWarning

def village_boundary():
    shrug = ee.FeatureCollection('users/jaltolwelllabs/SHRUG/Jharkhand')
    return shrug.filter(ee.Filter.And(
        ee.Filter.eq('district_n', 'saraikela kharsawan'),
        ee.Filter.eq('subdistric', 'gobindpur rajnagar'),
        ee.Filter.eq('village_na', 'namibera')
    ))


def encode_url(base_url, params):
    query_string = urlencode(params)
    return f"{base_url}?{query_string}"

def fetch_data(url, headers):
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else {}

# async def post_request(url, payload, session, year):
#     async with session.post(url, json=payload) as response:
#         if response.headers['Content-Type'] == 'application/json':
#             return {year: await response.json()}
#         else:
#             return {year: {"error": "Unexpected content type", "content": await response.text()}}
def fetch_data_post(url, headers, data):
    response = requests.post(url, headers=headers, json=data, verify=False)
    return response.json() if response.status_code == 200 else None

def distance(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371.0  # Radius of the Earth in kilometers

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c

def gen_data_payload(start_date, end_date, state_name):
    return {"stnVal":{
        "Agency_name":"CGWB",
        "Child":"All",
        "Startdate": start_date,
        "Enddate": end_date,
        "Parent": f"\"'{state_name}'\"",
        "Reporttype": "GWL data",
        "Station": "All",
        "Timestep": "Daily",
        "View": "Admin",
        "file_name": "Sample"
    }}


def station_location(coordinates):
    long, lat = zip(*coordinates)
    min_long, max_long, min_lat, max_lat = min(long), max(long), min(lat), max(lat)
    payload = {
        "where": "agency_name='CGWB'",
        "geometry": '{"spatialReference":{"latestWkid":4326,"wkid":4326},"xmin":'+str(min_long)+',"ymin":'+str(min_lat)+',"xmax":'+str(max_long)+',"ymax":'+str(max_lat)+'}',
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "units": "esriSRUnit_Foot",
        "inSR": 4326,
        "outFields": "*",
        "returnGeometry": True,
        "returnTrueCurves": False,
        "outSR": 4326,
        "returnIdsOnly": False,
        "returnCountOnly": False,
        "orderByFields": "objectid ASC",
        "returnZ": False,
        "returnM": False,
        "returnDistinctValues": False,
        "featureEncoding": "esriDefault",
        "f": "geojson"
    }
    encoded_url = encode_url(station_url, payload)
    response = fetch_data(encoded_url, headers={'Content-Type': 'application/json'})
    return (
        {feat['properties']['station_name']:feat['geometry']['coordinates'] for feat in response['features']},
        {feat['properties']['state_name'] for feat in response['features']}
    )


def close_stations(roi_centroid, stations):
    queue = deque()
    dist_stations = {}
    for station, station_coord in stations.items():
        dist = distance(roi_centroid, station_coord)
        dist_stations[dist] = station
    # print(dist_stations)
    sorted_dists = sorted(dist_stations)
    for k in sorted_dists:
        queue.append(dist_stations[k])
    return queue


# async def fetch_GWL_data(years, state_set):
#     tasks = []
#     async with aiohttp.ClientSession() as session:
#         for year in years:
#             for statename in state_set:
#                 payload = gen_data_payload(f'{year}-07-01', f'{year+1}-07-01', statename)
#                 tasks.append(post_request(data_url, payload, session, year))
#         return await asyncio.gather(*tasks)
def fetch_GWL_data(years, state_set):
    result = []
    for year in years:
        for statename in state_set:
            payload = gen_data_payload(f'{year}-07-01', f'{year+1}-07-01', statename)
            response = fetch_data_post(data_url, headers={'Content-Type': 'application/json'}, data=payload)
            result.append({year: response})
    return result

def groundwaterlevel(village_id, buff_dist, start_year, end_year):
    village_fc = village_boundary() # replace this with get village function
    buffer = village_fc.geometry().buffer(buff_dist).getInfo()
    stations, state_set = station_location(buffer['coordinates'][0])
    # print(state_set)
    # if there are no stations in 10km buffer of the village raise error
    if not stations: raise ValueError("No stations found in the specified area.")
    roi_centroid = village_fc.geometry().centroid().getInfo()['coordinates']
    stations_queue = close_stations(roi_centroid, stations)
    years = range(start_year, end_year+1)
    year_values = {k:[] for k in years}
    # gwl_data = asyncio.run(fetch_GWL_data(years, state_set))
    gwl_data = fetch_GWL_data(years, state_set)
    # print(gwl_data)
    processed_years = []
    for station in stations_queue:
        processed_years.extend(
            [year for year, val_list in year_values.items() if val_list]
        )
        for result in gwl_data:
            for year, data in result.items():
                if year in processed_years: continue
                if "error" not in data:
                    for entry in data:
                        if entry['Station_name'] == station:
                            for data in entry['Data']:
                                year_values[year].append(data['level'])
    # print(year_values)
    return {k:{'min':min(v,default=None), 'max':max(v,default=None)} for k,v in year_values.items()}

if __name__ == '__main__':
    start = time.perf_counter()
    output = groundwaterlevel(None, 10000, 2017, 2022) # 10km buffer
    print(output)
    end = time.perf_counter()
    print(f"Finished in {end-start} seconds")