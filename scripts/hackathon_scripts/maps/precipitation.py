import ee
ee.Initialize()
from datetime import datetime
import pandas as pd
from pathlib import Path
from itertools import product

start_year = 2014
end_year = 2022
collection_name = 'Precipitation'
collection = ee.ImageCollection("users/jaltolwelllabs/IMD/rain")

dist_list = [
    ('Anantapur', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Anantapur')),
    ('Dhamtari', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Dhamtari')),
    ('Kanker', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Kanker')),
    # ('Karauli', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Karauli')),
    ('Koppal', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Koppal')),
    ('Palghar', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Palghar')),
    ('Raichur', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Raichur')),
]

for dist_name, fc in dist_list:
    for year in range(start_year, end_year):
        fil = collection.filterDate(ee.Date.fromYMD(year, 6, 1), ee.Date.fromYMD(ee.Number(year).add(1), 6, 1))
        sum_im = fil.sum().set('system:time_start', ee.Date.fromYMD(year, 6, 1).millis()).clipToCollection(fc)
        task = ee.batch.Export.image.toDrive(image=sum_im,
                                        description=f'{dist_name}-{collection_name}-{year}-HydYear',
                                        folder='precipitation',
                                        region=fc.geometry(),
                                        scale=1000)
        task.start()

