import ee
ee.Initialize()

images_list =[
    ('org_carbon', ee.Image("OpenLandMap/SOL/SOL_ORGANIC-CARBON_USDA-6A1C_M/v02").multiply(5)),
    ('clay', ee.Image("OpenLandMap/SOL/SOL_CLAY-WFRACTION_USDA-3A1A1A_M/v02")),
    ('bulk_density', ee.Image("OpenLandMap/SOL/SOL_BULKDENS-FINEEARTH_USDA-4A1H_M/v02").multiply(10)),
    ('texture', ee.Image("OpenLandMap/SOL/SOL_TEXTURE-CLASS_USDA-TT_M/v02")),
]
band_nums = [0, 10, 30, 60, 100, 200]

dist_list = [
    # ('Anantapur', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Anantapur')),
    # ('Dhamtari', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Dhamtari')),
    # ('Kanker', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Kanker')),
    # ('Karauli', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Karauli')),
    # ('Koppal', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Koppal')),
    # ('Palghar', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Palghar')),
    ('Raichur', ee.FeatureCollection('users/jaltolwelllabs/hackathonDists/Raichur')),
]

for dist_name, fc in dist_list:
    for image_name, image in images_list:
        for band in band_nums:
            im = image.select([f'b{band}']).clipToCollection(fc)
            task = ee.batch.Export.image.toDrive(image=im,
                                    description=f'{dist_name}-{image_name}-depth{band}cm',
                                    folder='soil_properties',
                                    region=fc.geometry(),
                                    scale=250)
            task.start()
