"""Migrate ee.Image assets from one accessible ee.ImageCollection to
another accessible ee.ImageCollection
"""
import sys
from subprocess import check_output
import time


def main(source, dest, last_image=None):
    """Migrate Images from source ImageCollection to dest ImageCollection
    Note:- give read and write Permissions to respective source and dest

    Args:
        source (ee.ImageCollection): Asset id of the ImageCollection
        dest (ee.ImageCollection): Asset id of the ImageCollection
        last_image (str): name of the last image copied successfully, use this
        in case of any interuptions occured (maybe due to internet issues)

    Example:
    python Code/atree/scripts/asset_migration.py users/jaltol/ET_new/etSSEBop users/jaltolwelllabs/ET/etSSEBop

    Note:
    The python earthengine package to be authenticated with user having read
    access to source or the source is open (read) to all and write access to 
    the destination
    """
    list_source_cmd = f'earthengine ls {source}'
    source_response = check_output(list_source_cmd, shell=True)
    list_source = source_response.decode('utf-8').split('\r\n')
    if last_image:
        source_path = list_source[0].split('/')
        _ = source_path.pop()
        source_path = "/".join(source_path)
        cont_index = list_source.index(f'{source_path}/{last_image}') + 1
        list_source = list_source[cont_index:]
    for asset in list_source:
        if asset:
            name = asset.split('/')[-1]
            cp_cmd = f'earthengine cp {asset} {dest}/{name}'
            print(cp_cmd)
            _ = check_output(cp_cmd, shell=True)
            print(f'completed {name}')
            time.sleep(1) # to prevent any error due to immediate execution
    print('\ncompleted!!!')


if __name__ == '__main__':
    source = sys.argv[1]
    dest = sys.argv[2]
    try:
        last_name = sys.argv[3]
    except Exception:
        last_name = None
    main(source, dest, last_name)
