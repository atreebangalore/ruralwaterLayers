from qgis.utils import iface

village_check = ['sanbal', 'rampur']

lyr = iface.activeLayer()
print(f'Layer: {lyr.name()}')

village_list = [feat['village_na'] for feat in lyr.getFeatures()]

village_list = list(filter(lambda x: x != NULL, village_list))

print(village_list)

if village_check:
    for village in village_check:
        print(f'{village} present: {village in village_list}')
