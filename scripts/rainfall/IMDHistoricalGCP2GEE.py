# credits Qiusheng Wu : https://groups.google.com/g/google-earth-engine-developers/c/h5PZOmU_dfw/m/50MMDvOVAwAJ

import os,sys
from datetime import date,datetime,timedelta,timezone
import time
from subprocess import check_output
import re

def main():
    """uploads images from GCP to GEE Assets in batch
    """
    year = sys.argv[1]
    bucketname = sys.argv[2]
    geeuser = sys.argv[3]
    geecoll = sys.argv[4]
    
    bucket = 'gs://' + bucketname + "/"
    print("bucket url: ",bucket)
    ee_img_col = 'users' + '/' + geeuser + '/' + geecoll
    print("ee image coll path: ",ee_img_col)
    
    gs_command = 'gsutil ls ' + bucket + year + '*.tif'    # list gs tif files for particular year
    gs_tiffs = os.popen(gs_command,mode='r').read().strip().split('\n')
    print('Total number of files: {}'.format(len(gs_tiffs)))
    
    li = []
    
    for tif in gs_tiffs:
        print("copying from GCP bucket: ",tif)
        fbname = tif.replace(bucket, '').replace('.tif', '')  # get image name
        dt = datetime.strptime(fbname,"%Y%m%d").replace(tzinfo=timezone.utc).timestamp() * 1000    #.strftime("%Y-%m-%dT%H:%M:%S")
        print("setting property 'system:time_start' :", dt)
        eename = ee_img_col + "/" + fbname   
        print("copying to GEE Image Collection: ", eename)
        ee_command = 'earthengine upload image --asset_id=' + eename + ' ' + tif + ' --nodata_value=-999' + ' --time_start=' + str(int(dt))
        print(ee_command)
        output = check_output(ee_command)
        print(output)
        
if __name__=='__main__':
    main()