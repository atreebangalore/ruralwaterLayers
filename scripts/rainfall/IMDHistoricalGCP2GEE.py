"""
uploads the tif images from the Google Cloud Platform to GEE Assets for a specified 
year.
This script requires gsutil and earthengine cli to be installed, authenticated 
and configured.
Make sure the gsutil is configured with GCP bucket and has necessary permissions
for the authenticated user or the GCP bucket should have public access
and also earthengine cli should be authenticated with user having permissions to
modify the GEE image collection
"""
import os,sys
from datetime import datetime,timezone
from subprocess import check_output
# credits Qiusheng Wu : https://groups.google.com/g/google-earth-engine-developers/c/h5PZOmU_dfw/m/50MMDvOVAwAJ

def main():
    """uploads images from GCP to GEE Assets in batch
    
    Usage:
    python Code/atree/scripts/rainfall/IMDHistoricalGCP2GEE.py [year] [bucketname] [geeuser] [geecoll] [contd]
    
    Args:
    year (string): year of the tif images (YYYY)
    bucketname (string): name of the Google Cloud Platform bucket
    geeuser (string): Google Earth Engine UserName
    geecoll (string): Google Earth Engine Collection name
    contd (string)(optional): Last uploaded Image name for continuation (YYYYMMDD)
    
    Info:
    if the collection for geecoll is inside a folder, then the path should me
    entered (GEEfolderName/GEEcollectionName)
    contd - (optional) for continuation from the previously uploaded image in 
    case of unaccounted inturruption during execution of script for a year.
    
    Output:
    Google Earth Engine Assets
    """
    year = sys.argv[1]
    bucketname = sys.argv[2]
    geeuser = sys.argv[3]
    geecoll = sys.argv[4]
    try:
        contd = sys.argv[5]
        contd = 'gs://' + bucketname + "/" + contd + ".tif"
        print(contd)
    except:
        contd = None
    
    bucket = 'gs://' + bucketname + "/"
    print("bucket url: ",bucket)
    ee_img_col = 'users' + '/' + geeuser + '/' + geecoll
    print("ee image coll path: ",ee_img_col)
    
    gs_command = 'gsutil ls ' + bucket + year + '*.tif'    # list gs tif files for particular year
    gs_tiffs = os.popen(gs_command,mode='r').read().strip().split('\n')
    print('Total number of files: {}'.format(len(gs_tiffs)))
    
    if contd:
        index = gs_tiffs.index(contd)
        gs_tiffs = gs_tiffs[index:]
        print("files remaining to upload: ",len(gs_tiffs))
        
    for tif in gs_tiffs:
        print("copying from GCP bucket: ",tif)
        fbname = tif.replace(bucket, '').replace('.tif', '')  # get image name
        dt = datetime.strptime(fbname,"%Y%m%d").replace(tzinfo=timezone.utc).timestamp() * 1000    #.strftime("%Y-%m-%dT%H:%M:%S")
        print("setting property 'system:time_start' :", dt)
        eename = ee_img_col + "/" + fbname   
        print("copying to GEE Image Collection: ", eename)
        ee_command = 'earthengine upload image --asset_id=' + eename + ' ' + tif + ' --nodata_value=-999' + ' --time_start=' + str(int(dt))
        print(ee_command)
        output = check_output(ee_command, shell=True)
        print(output)
        
if __name__=='__main__':
    main()