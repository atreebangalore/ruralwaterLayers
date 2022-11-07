"""Module to filter a GEE image collection
"""

from ..config.gee_assets import iCol
from typing import Optional

try:
    import ee
    ee.Initialize()
except:
    "earthengine-api not working check internet"

class GEEIC:
    """
    """

    def __init__(self,icname: str, geometry: ee.Geometry) -> None:
        self.ic = iCol[icname]
        self.geometry = geometry

    def filterHydroYear(self,year: int) -> ee.ImageCollection:
        """ get a subset of the gee image collection for a hydrological year        
        """

        self.hydro_collection = self.ic.filterBounds(self.geometry).filterDate(
            ee.Date.fromYMD(year,6,1),
            ee.Date.fromYMD(year+1,6,1)
        )
        return self.hydro_collection

    def filterMonthYearRange(
        self,
        start_month: int,
        start_year: int, 
        end_month: Optional[int] = None,
        end_year: Optional[int] = None
        ) -> ee.ImageCollection:

        """get a subset of the gee image collection for a month , year 
        """
        
        if end_month is None:
            end_month = start_month
        if end_year is None:
            end_year = start_year
        
        self.myfilter = ee.Filter.And(
            ee.Filter.date(
            ee.Date.fromYMD(start_year,start_month,1),                     # e.g. 2016,10,1
            ee.Date.fromYMD(end_year,end_month,1).getRange('month').end()  # e.g. 2020,5,31
        ),
            ee.Filter.calendarRange(start_month,end_month,'month')
        )

        self.my_collection = self.ic.filterBounds(
            self.geometry
            ).filter(self.myfilter)

        return self.my_collection

    def filterS1EndMonsoon(
        self,
        year = int,
        start_month: Optional[int] = 9,
        end_month: Optional[int] = 10
    ) -> ee.ImageCollection:
        
        """get a subset for a given year for the post monsoon months
        """

        self.emfilter = ee.Filter.And(
            ee.Filter.calendarRange(year,year,'year'),
            ee.Filter.calendarRange(start_month,end_month,'month'),
            ee.Filter.eq('instrumentMode', 'IW'),
            ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'),
            ee.Filter.eq('orbitProperties_pass', 'DESCENDING')
        )

        self.em_collection = self.ic.filterBounds(
            self.geometry
        ).filter(self.emfilter).select(['VH'])

        return self.em_collection

