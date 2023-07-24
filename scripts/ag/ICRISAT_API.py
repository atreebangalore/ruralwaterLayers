"""extract data from ICRISAT API
http://data.icrisat.org/dldAPI/
you just need to input the API endpoint
Raises:
    KeyError: API request failed or info not availble in retrieved data
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import requests

URL = "http://data.icrisat.org"
dataFol = Path.home().joinpath("Data", "soil")
dataFol.mkdir(parents=True, exist_ok=True)


def get_data_from_api(url: str) -> Optional[Dict[str, Any]]:
    """retrieve data from the API endpoint

    Args:
        url (str): URL for the API

    Returns:
        Optional[Dict[str, Any]]: API data as Dictionary
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during API request: {e}")
        return None


def data_check(data: Dict[str, Any]) -> None:
    """check for headers in the retrieved data

    Args:
        data (Dict[str, Any]): Data from retrieved from the URL

    Raises:
        KeyError: API request failed or info not availble in retrieved data
    """
    headers = ["description", "headers", "data"]
    for header in headers:
        if header in data:
            print(f"{header} availability checked.")
        else:
            raise KeyError(f"{header} not found in the API response.")


def generate_heading(headers_list: List[Dict[str, str]]) -> List[str]:
    """Get the headers and corresponding unit from API data and create a
    list of heading for the CSV

    Args:
        headers_list (List[Dict[str, str]]): value of headers key in the data retrieved

    Returns:
        List[str]: heading as list for CSV
    """
    return [f"{i['header']}({i['unit']})" for i in headers_list]


def process(
    headers_list: List[str], data_list: List[List[str]]
) -> Dict[int, Dict[str, Any]]:
    """process the data into a dictionary suitable for creating Pandas DataFrame

    Args:
        headers_list (List[str]): list of Headings
        data_list (List[List[str]]): value of data key in the retrieved data

    Returns:
        Dict[int, Dict[str, Any]]: output Dictionary
    """
    return {ix: dict([*zip(headers_list, entry)]) for ix, entry in enumerate(data_list)}


def export(df_dict: Dict[int, Dict[str, Any]], filename: str) -> None:
    """export the output dictionary as CSV

    Args:
        df_dict (Dict[int, Dict[str, Any]]): output Dictionary
        filename (str): file name for the CSV to be saved
    """
    df = pd.DataFrame(df_dict).T
    out_path = dataFol.joinpath(f"{filename}.csv")
    df.to_csv(out_path, index=False)
    print(f"output: {out_path}")


def main(api_endpoint: str) -> None:
    """extract data from ICRISAT API and save the data as CSV
    http://data.icrisat.org/dldAPI/

    python Code/atree/scripts/ag/ICRISAT_API.py [api_endpoint]

    example:
        python Code/atree/scripts/ag/ICRISAT_API.py /dldAPI/unapportioned/fertilizer-consumption

    Args:
        api_endpoint (str): url for required data from http://data.icrisat.org/dldAPI/
    """
    url = URL + api_endpoint
    data = get_data_from_api(url)
    if data:
        data_check(data)
        filename = (
            data["description"]
            .replace("-wise", "")
            .replace(" : ", "_")
            .replace(" ", "_")
        )
        heading_list = generate_heading(data["headers"])
        df_dict = process(heading_list, data["data"])
        export(df_dict, filename)
    else:
        print("Terminated: API request failed")


if __name__ == "__main__":
    api_endpoint = sys.argv[1]
    main(api_endpoint)
