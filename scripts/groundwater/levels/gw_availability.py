import pandas as pd
import sys
import ee
ee.Initialize()


def get_status(st_name, year, month):
    url = 'https://github.com/atreebangalore/ruralwaterLayers/raw/master/scripts/groundwater/levels/India-WRIS%20GW%20Download%20Status.csv'
    df = pd.read_csv(url)
    df.set_index('STATE', inplace=True)

    st_dict = {
        'ANDHRA PRADESH': 'Andhra Pradesh',
        'ARUNACHAL PRADESH': 'Arunachal Pradesh',
        'ASSAM': 'Assam',
        'BIHAR': 'Bihar',
        'CHANDIGARH': 'Chandigarh',
        'CHHATTISGARH': 'Chhattisgarh',
        'DADRA & NAGAR HAVELI': 'Dadara & Nagar Havelli',
        'DELHI': 'NCT of Delhi',
        'DAMAN & DIU': 'Daman & Diu',
        'GOA': 'Goa',
        'GUJARAT': 'Gujarat',
        'HARYANA': 'Haryana',
        'HIMACHAL PRADESH': 'Himachal Pradesh',
        'JAMMU & KASHMIR': 'Jammu & Kashmir',
        'JHARKHAND': 'Jharkhand',
        'KARNATAKA': 'Karnataka',
        'KERALA': 'Kerala',
        'LADAKH': '',
        'MADHYA PRADESH': 'Madhya Pradesh',
        'MAHARASHTRA': 'Maharashtra',
        'MANIPUR': 'Manipur',
        'MEGHALAYA': 'Meghalaya',
        'MIZORAM': 'Mizoram',
        'NAGALAND': 'Nagaland',
        'ODISHA': 'Odisha',
        'PONDICHERRY': 'Puducherry',
        'PUNJAB': 'Punjab',
        'RAJASTHAN': 'Rajasthan',
        'SIKKIM': 'Sikkim',
        'TAMILNADU': 'Tamil Nadu',
        'TELANGANA': 'Telangana',
        'TRIPURA': 'Tripura',
        'UTTAR PRADESH': 'Uttar Pradesh',
        'UTTARAKHAND': 'Uttarakhand',
        'WEST BENGAL': 'West Bengal',
    } # csv : feature_collection_datameet

    gw_coll = ee.ImageCollection('users/jaltol/GW/IndiaWRIS')
    f_coll = ee.FeatureCollection("users/cseicomms/boundaries/datameet_districts_boundary_2011")
    ST_col = 'ST_NM'

    f_filtered = f_coll.filter(ee.Filter.eq(ST_col, st_dict[st_name.upper()]))
    if not f_filtered.size().getInfo():
        raise ValueError('State name provided does not match any feature.')
    gw_filtered = gw_coll.filterBounds(f_filtered).filterDate(
        ee.Date.fromYMD(year, month, 1).getRange('month'))

    gw_image_size = int(gw_filtered.size().getInfo())
    gw_sheet_list = df[str(year)][st_name.upper()].replace(' ', '').split('&')

    if not gw_image_size:
        return 'Unavailable'
    elif str(month) in gw_sheet_list:
        return 'Available'
    else:
        return 'Interpolated'


if __name__ == '__main__':
    st_name = sys.argv[1]
    year = int(sys.argv[2])
    month = int(sys.argv[3])
    status = get_status(st_name, year, month)
    print(f'Availability Status: {status}')
