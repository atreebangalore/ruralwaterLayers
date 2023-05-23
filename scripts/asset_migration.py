"""Migrate ee.Image assets from one accessible ee.ImageCollection to
another accessible ee.ImageCollection
"""
import sys
from subprocess import check_output
import time
from typing import List, Optional


def execute_copy(cp_cmd: str) -> None:
    """subprocess execution of earthengine copy command

    Args:
        cp_cmd (str): command
    """
    check_output(cp_cmd, shell=True)


def images_list(source: str) -> List[str]:
    """get the list of images available in the ImageCollection

    Args:
        source (str): Asset id of the ImageCollection

    Returns:
        List[str]: List of images in the ImageCollection
    """
    list_source_cmd = f'earthengine ls {source}'
    source_response = check_output(list_source_cmd, shell=True)
    return source_response.decode('utf-8').split('\r\n')


def ee_abs_path(abs_image_path: str) -> str:
    """Get the absolute path of the ImageCollection

    Args:
        ee_asset_path (str): absolute path of Image in a collection

    Returns:
        str: absolute path of the ImageCollection
    """
    source_path = abs_image_path.split('/')
    _ = source_path.pop()
    return "/".join(source_path)


def main(source:str, dest:str, last_image:Optional[str]=None):
    """Migrate Images from source ImageCollection to dest ImageCollection
    Note:- give read and write Permissions to respective source and dest

    python Code/atree/scripts/asset_migration.py [source] [dest] [last_image]

    Args:
        source (str): Asset id of the ImageCollection
        dest (str): Asset id of the ImageCollection
        last_image (Optional[str]): name of the last image copied successfully, use this
        in case of any interuptions occured (maybe due to internet issues)

    Example:
    python Code/atree/scripts/asset_migration.py users/jaltol/ET_new/etSSEBop users/jaltolwelllabs/ET/etSSEBop

    Note:
    The python earthengine package to be authenticated with user having read
    access to source or the source is open (read) to all and write access to 
    the destination
    """
    list_source = images_list(source)
    list_dest = images_list(dest)
    if last_image:
        source_path = ee_abs_path(list_source[0])
        dest_path = ee_abs_path(list_dest[0])
        if f'{source_path}/{last_image}' not in list_source or f'{dest_path}/{last_image}' not in list_dest:
            raise ValueError(f'{last_image} not copied over successfully')
        cont_index = list_source.index(f'{source_path}/{last_image}') + 1
        list_source = list_source[cont_index:]
    for asset in list_source:
        if asset:
            name = asset.split('/')[-1]
            cp_cmd = f'earthengine cp {asset} {dest}/{name}'
            print(cp_cmd)
            count, not_completed = 0, True
            while not_completed: # Remote Connection terminated error
                try:
                    execute_copy(cp_cmd)
                    not_completed = False
                except Exception as e:
                    print(f'failed execution {name}, retrying! {count}')
                    count += 1
                    if count == 6:
                        raise e
                    time.sleep(60)
            print(f'completed {name}')
            time.sleep(1)  # to prevent any error due to immediate execution
    print('\ncompleted!!!')


if __name__ == '__main__':
    source = sys.argv[1]
    dest = sys.argv[2]
    try:
        last_name = sys.argv[3]
    except Exception:
        last_name = None
    main(source, dest, last_name)
