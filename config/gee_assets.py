"""Dictionary References to Google Earth Engine Assets
"""

try:
    import ee
    ee.Initialize()
except:
    "earthengine-api not working, check internet connection"


img = {
    'aquifers': ee.Image('users/jaltol/GW/sy_mean_cgwb'),
    'sw': ee.Image("JRC/GSW1_3/GlobalSurfaceWater"),
    'srtm': ee.Image("USGS/SRTMGL1_003"),
}

iCol = {
    'rainNRT': ee.ImageCollection("users/jaltol/IMD/rainNRT"),
    'rain': ee.ImageCollection("users/jaltol/IMD/rain"),
    'maxT': ee.ImageCollection("users/jaltol/IMD/maxTemp"),
    'minT': ee.ImageCollection("users/jaltol/IMD/minTemp"),
    'dw': ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1"),
    'et': ee.ImageCollection("users/jaltol/ET_new/etSSEBop"),
    'refET': ee.ImageCollection('users/jaltol/ET_new/refCropET'),
    'gw' : ee.ImageCollection("users/jaltol/GW/IndiaWRIS"),
    's1': ee.ImageCollection("COPERNICUS/S1_GRD"),
    's2': ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED"),
    'swmh': ee.ImageCollection("JRC/GSW1_3/MonthlyHistory"),
    'swyh': ee.ImageCollection("JRC/GSW1_3/YearlyHistory")
}

fCol = {
    'dist2011': ee.FeatureCollection("users/jaltol/FeatureCol/District_Map_2011")
}


# this section for ruralwaterlayers scripts

iCollDict = {
    'evapotranspiration': ee.ImageCollection("users/cseicomms/evapotranspiration_ssebop"),
    'rainfall': ee.ImageCollection("users/cseicomms/rainfall_imd"),
    'groundwater_levels': ee.ImageCollection("users/cseicomms/groundwater/levels"),
}

fCollDict = {
    'districts': {
        'id': ee.FeatureCollection("users/cseicomms/boundaries/datameet_districts_boundary_2011"),
        'state_col': "ST_NM",
        'district_col': "DISTRICT"
    },
    'KAblocks': {
        'id': ee.FeatureCollection("users/jaltol/FeatureCol/Karnataka_Block_Typologies_2015_2020"),
        'block_col': 'CD_Block_N'
    },
    'KAcommandarea': {
        'id': ee.FeatureCollection('users/jaltol/FeatureCol/Karnataka_CommandArea')
    },
    'KAnoncommandarea': {
        'id': ee.FeatureCollection('users/jaltol/FeatureCol/Karnataka_NonCommandArea')
    }
}

statDict = {
    'total': ee.Reducer.sum(),
    'mean': ee.Reducer.mean(),
    'median': ee.Reducer.median(),
    'max': ee.Reducer.max(),
    'min': ee.Reducer.min()
}
