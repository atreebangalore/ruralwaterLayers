import requests
import sys
from typing import Optional, List, Dict, Any

URL = "http://data.icrisat.org"

def get_data_from_api(url: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API request: {e}")
        return None

def data_check(data: Dict[str, Any]) -> None:
    headers = ['description', 'headers', 'data']
    for header in headers:
        if header in data:
            print(f'{header} availability checked.')
        else:
            raise KeyError(f'{header} not found in the API response.')

def generate_heading(headers_list: List) -> List:
    return [f"{i['header']}({i['unit']})" for i in headers_list]

def process(headers_list: List, data_list: List) -> Dict[int, Dict[str, Any]]:
    return {
        ix: dict([*zip(headers_list, entry)])
        for ix, entry in enumerate(data_list)
    }

def main(api_endpoint: str) -> None:
    # /dldAPI/unapportioned/fertilizer-consumption
    url = URL+api_endpoint
    data = get_data_from_api(url)
    if data:
        data_check(data)
        filename = data['description'].replace('-wise','').replace(' : ','_').replace(' ','_')
        heading_list = generate_heading(data['headers'])
        df_dict = process(heading_list, data['data'])
    else:
        print("Terminated: API request failed")

if __name__=='__main__':
    api_endpoint = sys.argv[1]
    main(api_endpoint)
