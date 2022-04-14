import ee
ee.Initialize()

iCollDict = {
      'evapotranspiration':ee.ImageCollection("users/cseicomms/evapotranspiration_ssebop"),
      'rainfall':ee.ImageCollection("users/cseicomms/rainfall_imd"),
      'groundwater_levels':ee.ImageCollection("users/cseicomms/groundwater/levels"),
    }

fCollDict = {
 'districts': {
     'id': ee.FeatureCollection("users/cseicomms/boundaries/datameet_districts_boundary_2011"),
     'state_col': "ST_NM",
     'district_col':"DISTRICT"
 }
}

statDict = {
      'total':ee.Reducer.sum(),
      'mean':ee.Reducer.mean(),
      'median':ee.Reducer.median(),
      'max':ee.Reducer.max(),
      'min':ee.Reducer.min()
    }