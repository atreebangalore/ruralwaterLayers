import json
import io
import copy
from os import link
import shutil

from multiprocessing import Pool
from pathlib import Path
from numpy import Inf
import requests
from typing import List, Dict, Tuple

from bs4 import BeautifulSoup

# webpages
#
# https://github.com/ramSeraph/opendata/tree/master/jjm
#
# list of schemes and sources
# https://ejalshakti.gov.in/IMISReports/Reports/BasicInformation/rpt_SchemesSourcesGWSW_S.aspx?Rep=0&RP=Y
#
# water purification plants and contaminants
# https://ejalshakti.gov.in/IMISReports/Reports/BasicInformation/rpt_RWS_CommunityWaterPurificationPlant_S.aspx?Rep=0&RP=Y
#
# water quality testing
# https://ejalshakti.gov.in/IMISReports/Reports/TargetAchievement/rpt_WQM_WaterQualityTestingInLabs_S.aspx?Rep=0&RP=Y&APP=IMIS
#
# JJM Dashboard & FHTC
# https://ejalshakti.gov.in/jjmreport/JJMIndia.aspx


class Info():
    JJMPATH = Path.home().joinpath('Code', 'atree', 'data', 'jjm')
    SCHEMESURL = 'https://ejalshakti.gov.in/IMISReports/Reports/BasicInformation/rpt_SchemesSourcesGWSW_D.aspx?Rep=0'
    PUREURL = 'https://ejalshakti.gov.in/IMISReports/Reports/BasicInformation/rpt_RWS_CommunityWaterPurificationPlant_S.aspx?Rep=0&RP=Y'
    WQURL = 'https://ejalshakti.gov.in/IMISReports/Reports/TargetAchievement/rpt_WQM_WaterQualityTestingInLabs_S.aspx?Rep=0&RP=Y&APP=IMIS'
    FHTCURL = 'https://ejalshakti.gov.in/jjmreport/JJMIndia.aspx'

    def __init__(self) -> None:
        Info.JJMPATH.mkdir(parents=True, exist_ok=True)

    def get_base_header(self) -> Dict[str, str]:
        return {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Length': '22880',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Cookie': 'ASP.NET_SessionId=hw5omcemufyb4qjplm03cpox',
            'DNT': '1',
            'Host': 'ejalshakti.gov.in',
            'Origin': 'https://ejalshakti.gov.in',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.26',
            'X-MicrosoftAjax': 'Delta=true',
            'X-Requested-With': 'XMLHttpRequest',
            'sec-ch-ua': '"Microsoft Edge";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-gpc': '1',
        }

    def get_form_data(self, param: str) -> Dict[str, str]:
        ref_dict = {
            'SCHEMES': {
                'ctl00$ScriptManager1': 'ctl00$upPnl|ctl00$ContentPlaceHolder$btnGO',
                'ctl00$ddLanguage': '',
                'ctl00$ContentPlaceHolder$ddState': '',  # State value
                '__EVENTTARGET': '',
                '__EVENTARGUMENT': '',
                '__LASTFOCUS': '',
                '__ASYNCPOST': 'true',
                'ctl00$ContentPlaceHolder$btnGO': 'Show'
            },
        }
        return ref_dict[param]


class JJM(Info):
    def __init__(self) -> None:
        super().__init__()

    def get_base_form_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        hidden_inputs = soup.find_all('input', {'type': 'hidden'})
        base_form_data = {}
        for inp in hidden_inputs:
            ident = inp.attrs['id']
            val = inp.attrs.get('value', '')
            base_form_data[ident] = val
        return base_form_data

    def get_soup(self, base_url: str) -> Tuple[requests.sessions.Session, BeautifulSoup]:
        session = requests.session()
        resp = session.get(base_url)
        if not resp.ok:
            raise IOError(f'failed to get data from {base_url}')
        soup = BeautifulSoup(resp.text, 'html.parser')
        return session, soup

    def get_state_details(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        table = soup.find('table', {'class': 'SelectData'})
        if not table:
            table = soup.find('div', {'id': 'Div1'})
        state_select = table.find(
            'select', {'id': 'ContentPlaceHolder_ddState'})
        state_options = state_select.find_all('option')
        return [(s_option.attrs['value'], s_option.text) for s_option in state_options]


class Schemes(JJM):
    def __init__(self) -> None:
        super().__init__()
        self.session, self.soup = self.get_soup(self.SCHEMESURL)

    def get_input_details(self) -> List[Tuple[str, str]]:
        self.state_vals_names = self.get_state_details(self.soup)
        return self.state_vals_names

    def get_basics(self) -> None:
        self.base_form_data = self.get_base_form_data(self.soup)
        self.base_header = self.get_base_header()
        self.base_header['Referer'] = self.SCHEMESURL
        self.form_data = self.get_form_data('SCHEMES')
        self.form_data.update(self.base_form_data)

    def get_data(self, state_value: str) -> BeautifulSoup:
        self.form_data.update(
            {'ctl00$ContentPlaceHolder$ddState': state_value})
        resp = self.session.post(
            self.SCHEMESURL, data=self.form_data, headers=self.base_header, allow_redirects=True)
        if not resp.ok:
            raise IOError('post to get district list failed')
        return BeautifulSoup(resp.text, 'html.parser')


if __name__ == '__main__':
    test = Schemes()
    states_list = test.get_input_details()
    test.get_basics()
    data = test.get_data('004')
    print(data)
