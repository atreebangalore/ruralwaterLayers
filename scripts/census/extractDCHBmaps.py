"""
given a DCHB pdf in the data/census directory,
example filename, 2810_PART_A_DCHB_KHAMMAM.pdf
will extract all the map images from the pdf corresponding
to block-wise village maps and saves them in a separate PDF
example filename, 2810_PART_A_DCHB_KHAMMAM_images.pdf
to-do: find ways to reduce run time, while keeping output file size small
"""

import os,sys
from pathlib import Path
import fitz
import re,glob

dataFol = Path.home().joinpath("Code","atree","data")
os.chdir(dataFol)
print(os.getcwd())


def main():
    """    
    Usage:
    python extractDCHBmaps.py [district]
    
    Args:
    district (str): name of district 
    
    Returns:
    a DCHB pdf with only the maps 
    
    """
    print("THIS SCRIPT TYPICALLY TAKES 5-7 min to run","\n")  
    
    district = sys.argv[1].upper()
    globs = os.getcwd()+"\census\*"+district+".pdf"
    print(globs)

    path = glob.glob(globs)[0]
    fn = Path(path)
        
    fnvd = fn.parent.joinpath(fn.stem + '_vill_dir' + fn.suffix)
    fnimg = fn.parent.joinpath(fn.stem + '_images' + fn.suffix)

    print(fnvd,fnimg)
    
    doc = fitz.open(fn)
    doc.save(fnvd)
    doc = fitz.open(fnvd)
    
    # returns page numbers of START and END of village directory 
    regex = "SECTION|I|VILLAGE|TOWN|DIRECTORY|\s|\n|-"
    startwith = None
    endwith = None
    doclen = doc.pageCount - 1

    for page in doc:
        text = page.get_text()
        res1 = page.search_for("SECTION")
        res2 = page.search_for("VILLAGE DIRECTORY")
        res3 = page.search_for("TOWN DIRECTORY")
        if (len(res1)>0 and len(res2)>0):
            tmp = re.sub(regex,"",text)
            if len(tmp)==0:
                startwith = page.number
        if (len(res1)>0 and len(res3)>0):
            tmp = re.sub(regex,"",text)
            if len(tmp)==0:
                endwith = page.number            

    doc.select([*range(startwith,endwith)])
    print("page count of just the village directory section",doc.pageCount)
    doc.saveIncr()
    
    li = []
    for page in doc:
        img = page.get_images()
        if len(img)>0:
            li.append(page.number)
    print("page numbers of images",li,
          "total number of images",len(li))
    doc.select(li)
    doc.save(fnimg,garbage=4)    # THIS TAKES TIME BUT REDUCES FILE SIZE

    
if __name__ == "__main__":
    main()