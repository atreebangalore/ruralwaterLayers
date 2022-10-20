import json
import io
import copy
from os import link
import shutil

from multiprocessing import Pool
from pathlib import Path
from numpy import Inf
import requests

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
    SCHEMESURL = 'https://ejalshakti.gov.in/IMISReports/Reports/BasicInformation/rpt_SchemesSourcesGWSW_S.aspx?Rep=0&RP=Y'
    def __init__(self) -> None:
        Info.JJMPATH.mkdir(parents=True, exist_ok=True)

class JJM(Info):
    def __init__(self) -> None:
        super().__init__()
    
    def get_base_form_data(self, soup):
        hidden_inputs = soup.find_all('input', { 'type': 'hidden' })
        base_form_data = {}
        for inp in hidden_inputs:
            ident = inp.attrs['id']
            val = inp.attrs.get('value', '')
            base_form_data[ident] = val
        return base_form_data

    def get_data(self, base_url):
        session = requests.session()
        resp = session.get(base_url)
        if not resp.ok:
            raise IOError(f'failed to get data from {base_url}')
        soup = BeautifulSoup(resp.text, 'html.parser')
        table = soup.find('table', {'class': 'SelectData'})
        state_select = table.find('select', {'id': 'ContentPlaceHolder_ddState'})
        state_options = state_select.find_all('option')
        state_map = {}
        for s_option in state_options:
            val = s_option.attrs['value']
            if val == '-1':
                continue
            else:
                print(s_option.text)
    

class Schemes(JJM):
    def __init__(self) -> None:
        super().__init__()
        print(self.JJMPATH)
        self.get_data(self.SCHEMESURL)


if __name__ == '__main__':
    test = Schemes()