"""calculation of water demand or Crop Water Requirement
"""
import os,sys
from pathlib import Path

root = Path.home().joinpath("Code","atree")
sys.path.append(root)

from config.placenames import ST_names, DT_names
from config.gee_assets import iCol
from libs.dynamic_world import DW
from config.crop_details import kc_dict, crop_period

import os
from pathlib import Path
import pickle
import pandas as pd
from datetime import datetime
from datetime import timedelta as td
from calendar import monthrange
from typing import List, Dict, Tuple, Union
from collections import defaultdict

try:
    import ee
    ee.Initialize()
except:
    "earthengine-api not working, check internet connection"

# plugin_path = os.path.split(os.path.dirname(__file__))[0]    # name_of_plugin_folder
# plugin_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

root = Path.home().joinpath("Code","atree")
sys.path.append(root)

class CropDetails:
    """get details of crops grown in the input geometry for a season or
    list of seasons provided.
    """

    def __init__(self, year: int, state: str, dist: str, season: Union[str, List[str]], geometry: ee.Geometry) -> None:
        self.geometry = geometry
        self.year = year
        self.state_n = state.title()
        self.state_abb = self.get_ST_abb()  # get abb from placenames
        self.dist_n = dist.title()
        self.season = [season] if type(season) == str else season.split()
        
        print("\n************************")
        print("state: ", self.state_n)
        print("district: ", self.dist_n)
        print("season: ",self.season)

    def get_ST_abb(self) -> str:
        """for the input state name get the two letter abbreviated name

        Returns:
            str: two letter abbreviated state name
        """
        for abb, st_list in ST_names.items():
            if self.state_n in st_list:
                return abb

    
    def get_crop_details(self, num_crops: int) -> Dict[str, Tuple[float, int, str, List[float], List[int]]]:
        """get the details of crops grown in the geometry. Output is dictionary.
        {crop: (area_ha, area%, sowing_date, KcList, GrowthPeriodList)}
        area in hectares
        sowing date in YYYY-MM-DD

        Args:
            num_crops (int): max number of crops required in the output

        Returns:
            Dict[str, Tuple[float, int, str, List[float], List[int]]]: dictionary of crop details
        """
        output = {}
        seasonal_dict = {
            'Kharif': (6, 9),
            'Rabi': (10, 1),
            'Summer': (2, 5),
            'Whole Year': (6,5)
        }
        for season in self.season:
            lulc = DW(self.year, self.geometry)
            historical = lulc.get_historical(5)    # returns a 5y ee.ImageCollection
            start, end = seasonal_dict[season]
            seasonal = lulc.get_seasonal(start, end, historical)    # returns a 5y seasonal ee.ImageCollection
            area_lulc = lulc.get_area_ha(4, seasonal)            # crops class - label = 4
            sowing_date = self.get_sowing_date(season)
            df = self.read_crop_details(season)
            df = df.sort_values(by=['perc'], ascending=False).head(num_crops).reset_index(drop=True)
            print("\n************************")
            df['area_lulc'] = (df['perc']/100) * area_lulc
            for _, row in df.iterrows():
                output[row['crop']] = (
                    round(row['area_lulc']),
                    row['perc'],
                    sowing_date,
                    self.get_kc_list(row['crop']),
                    self.get_period(row['crop']))
            output['total_area'] = area_lulc       
        return output

    def read_crop_details(self, season: str) -> pd.DataFrame:
        """read the Govt. dataset available in pickle format for the crop
        details filtered to the district of the geometry

        Args:
            season (str): season for which crop details required

        Returns:
            pd.DataFrame: DataFrame of the Crop details
        """
        
        fpath = os.path.join(root,'data','crops','allcrops-allseasons-allstates-201920.csv')
        csv = pd.read_csv(fpath)
        csv = csv[csv['state']==self.state_n]
        # print("column names: ",csv.columns)
        # print("size of csv subset: ",csv.shape)
        # print("csv states: ",csv['state'].unique())
        # print("csv districts: ",csv['district'].unique())

        if self.dist_n.upper() in set(csv['district'].values):
            dn = self.dist_n.upper()
            print("dn if:", dn)
        else:
            dist_dict = DT_names[self.state_abb]
            for abb, dist_list in dist_dict.items():
                if self.dist_n in dist_list:
                    for dist_sub in dist_list:
                        if dist_sub.upper() in set(csv['district'].values):
                            dn = dist_sub.upper()
                            print("dn else: ",dn)
        dist_crops = csv[(csv['district'] == dn) & (csv['season'] == season) & (csv['perc'] != 0)]
        print("no of crops found: ",len(dist_crops))

        return dist_crops

    def get_sowing_date(self, season: str) -> str:
        """get the default start date of sowing crop for the given season. 

        Args:
            season (str): croping season

        Returns:
            str: date of sowing for the season in YYYY-MM-DD
        """
        sowing_dict = {
            'Kharif': f'{self.year}-06-01',
            'Rabi': f'{self.year}-10-01',
            'Summer': f'{self.year+1}-02-01',
            'Whole Year': f'{self.year}-06-01'
        }
        return sowing_dict[season]

    def get_kc_list(self, crop: str) -> List[float]:
        """get the list of Kc values for a crop from the Kc database

        Args:
            crop (str): name of the crop

        Returns:
            List[float]: list of Kc values for the crop
        """
        return kc_dict[crop]

    def get_period(self, crop: str) -> List[int]:
        """get the list of growth periods for a crop from the Growth period
        database

        Args:
            crop (str): name of the crop

        Returns:
            List[int]: list of Growth period of different stages for the crop
        """
        return crop_period[crop]


class CWR:
    """get the Crop water requirement for the input crops grown in the geometry
    crop details input as dictionary
    {crop: (area_ha, area%, sowing date, KcList, GrowthPeriodList)}
    area in hectares
    sowing date in YYYY-MM-DD
    """

    def __init__(self, year: int, crop_details: Dict[str, Tuple[float, int, str, List[float], List[int]]]) -> None:
        self.year = year
        ### {crop: (area_ha, area%, sowing date, Kc, period)}  ###
        self.crop_dict = crop_details
        keys = ['06','07','08','09','10','11','12','01','02','03','04','05']
        self.ETc_monthwise = {k:{'total':0} for k in keys}    # **dict(zip(keys,values)) #why does this create references?

    def get_refET(self, geometry: ee.Geometry) -> Dict[str, float]:
        """get reference ET (ETo) month wise for a single hydrological year

        Args:
            geometry (ee.Geometry): geometry over which to calculate ETo

        Returns:
            Dict[str, float]: {month: ETo}
        """
        EToCol = iCol['refET']
        self.ETo_dict = {}  # {month: ETo}
        monthyearseq = self.mo_yr_seq(self.year)
        for period in monthyearseq:
            y, m = period
            image = EToCol.filterDate(ee.Date.fromYMD(
                y, m, 1).getRange('month')).first()
            self.ETo_dict[f'{m:02d}'] = round(image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=30,
                maxPixels=1e10
            ).getInfo()['b1'],2)
        return self.ETo_dict

    def get_refET_hist(self, geometry: ee.Geometry, yr_step: int) -> Dict[str, float]:
        """get reference ET (ETo) monthwise for hydrological years over past
        required no. of years

        Args:
            geometry (ee.Geometry): geometry over which to calculate ETo
            yr_step (int): no. of years to consider for ETo mean calculation

        Returns:
            Dict[str, float]: {month: ETo}
        """
        EToCol = iCol['refET']
        self.ETo_dict = {}  # {month: ETo}
        historical = EToCol.filterBounds(geometry).filterDate(ee.Date.fromYMD(
            self.year-yr_step, 6, 1), ee.Date.fromYMD(self.year+1, 6, 1))
        for m in range(1, 13):
            image = historical.filter(
                ee.Filter.calendarRange(m, m, 'month')).mean()
            self.ETo_dict[f'{m:02d}'] = round(image.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=geometry,
                scale=30,
                maxPixels=1e10
            ).getInfo()['b1'],2)
        return self.ETo_dict

    def get_Kc_monthly(self) -> Dict[str, Dict[str, float]]:
        """get Kc values weighted mean over months, monthly Kc values.

        Returns:
            Dict[str, Dict[str, float]]: {crop: {month: KcValue}}
        """
        self.crop_monthly_kc = {}  # {crop: {month: Kc}}
        for crop in self.crop_dict:
            monthdict = {f"{item:02d}": [] for item in range(1, 13)}
            area, p, start_date, crop_kc, crop_period = self.crop_dict[crop]
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            for stage in range(len(crop_kc)):
                end_date = start_date+td(days=crop_period[stage])
                date_range = pd.date_range(start_date, end_date)
                for idate in date_range:
                    monthdict[idate.strftime("%m")].append(crop_kc[stage])
                start_date = end_date + td(days=1)
            monthlyKc = {key: round(sum(value) / len(value), 2)
                         for key, value in monthdict.items() if value}
            self.crop_monthly_kc[crop] = monthlyKc
        return self.crop_monthly_kc

    def get_ETc(self) -> Tuple[Dict[str, float], Dict[str, float]]:
        """get the volumetric ETc for a crop in m3

        Returns:
            Dict[str, float]: {crop: ETc(m3)}
        """
        self.ETc_cropwise = defaultdict(dict)
        self.mmCropMonth = defaultdict(dict)

        mo_dy_dict = self.mo_range(self.year)
        for crop in self.crop_dict:
            area, p, start_date, crop_kc, crop_period = self.crop_dict[crop]
            self.ETc_cropwise[crop]['total'] = 0
            self.mmCropMonth[crop]['total'] = 0
            for month in self.crop_monthly_kc[crop]:
                ETc_month_mm = self.crop_monthly_kc[crop][month] * \
                    self.ETo_dict[month]*mo_dy_dict[month] #* (p/100)
                ETc_month_m3 = round(((ETc_month_mm * 1e-3) * (area * 1e4))) #mm*Ha -> m3
                
                self.mmCropMonth[crop][month] = ETc_month_mm
                self.mmCropMonth[crop]['total'] += ETc_month_mm
                self.ETc_cropwise[crop][month] = ETc_month_m3
                self.ETc_cropwise[crop]['total'] += ETc_month_m3
                self.ETc_monthwise[month][crop] = ETc_month_m3
                self.ETc_monthwise[month]['total'] += ETc_month_m3
            
        return (self.mmCropMonth,self.ETc_cropwise,self.ETc_monthwise)  # {crop: ETc(m3)}

    def mo_yr_seq(self, year: int) -> List[Tuple[int, int]]:
        """get a sequence of (year, month) for a hydrological year

        Args:
            year (int): start year of the hydrological year

        Returns:
            List[Tuple[int, int]]: list of tuples having year and month
        """
        monthseq = list(range(6, 13)) + list(range(1, 6))
        yearseq = [year]*7 + [year+1]*5
        return [*zip(yearseq, monthseq)]

    def mo_range(self, year: int) -> Dict[str, int]:
        """get number of days in a month for a hydrological year

        Args:
            year (int): start year of the hydrological year

        Returns:
            Dict[str, int]: {month: no_of_days}
        """
        seq = self.mo_yr_seq(year)
        mr_dict = {}
        for ele in seq:
            yr, mo = ele
            _, days = monthrange(yr, mo)
            mr_dict[f"{mo:02d}"] = days
        return mr_dict  # {month: no_of_days}