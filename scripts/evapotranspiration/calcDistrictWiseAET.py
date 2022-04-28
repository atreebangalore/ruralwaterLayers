"""
Calculates a districtwise AET using FAOs methodology
formula: AET = Kc*PET*Crop.Season.Group.Area

current: single district
future: make script accept multiple districts at a time
"""

import os, sys
from pathlib import Path
import pandas as pd

petExcelFile = "data/PET.csv"
cropGrAreaFile = "data/CropGroups_Area.csv"
kcFile = "data/Kc.csv"
petDf = pd.read_csv(petExcelFile)
cAreaDf = pd.read_csv(cropGrAreaFile)
kcDf = pd.read_csv(kcFile).fillna(0)
# print("PET columns:",petDf.columns,
#       "Kc columns::",kcDf.columns,
#       "CropA columns:",cAreaDf.columns,
#       sep="\n")
# print(kcDf.head())

def kcXpet(district):
    petDistrict = petDf[petDf['District']==district]
    kcDf_val = kcDf.loc[:,"Jan":"Dec"].values
    petD_val = petDistrict.loc[:,"Jan":"Dec"].values
    kcXpet = pd.DataFrame(kcDf_val * petD_val, columns=kcDf.loc[:,"Jan":"Dec"].columns, index=kcDf["Groups_Season"])
    kcXpet['District']=district
    kcXpet.to_csv("data/aet.csv",index=True)
    return kcXpet

def getCropsAET(district,aet):
    aetVal = aet.loc[:,"Jan":"Dec"].values *10 # 10000/1000 (ha-mm to m3)
    cArea = cAreaDf[["Groups_Season",district.upper()]]
    cAreaVal = cArea.loc[:,district.upper()].values
    cAreaVal = cAreaVal.reshape(222,1)
    aetM3 = pd.DataFrame(cAreaVal * aetVal, columns=aet.loc[:,"Jan":"Dec"].columns, index=cArea["Groups_Season"])
    aetM3.to_csv("data/aetM3.csv", index=True)
    aetM3sum = aetM3.sum()
    aetM3sum.to_csv("data/aetM3sum.csv", index=True)
    return aetM3sum

def calcDistSeasonArea(district):
    cga_bySea = cAreaDf.groupby("Season").sum()
    cga_bySea.to_csv("data/cga_bySea.csv")
    return cga_bySea
    
def calcDistMonthArea(district,cga_bySea):
    month_season_map = {"Jan":["Rabi","Whole year"],
                        "Feb":["Summer","Whole year"],
                        "Mar":["Summer","Whole year"],
                        "Apr":["Summer","Whole year"],
                        "May":["Summer","Whole year"],
                        "Jun":["Kharif","Whole year"],
                        "Jul":["Kharif","Whole year"],
                        "Aug":["Kharif","Whole year"],
                        "Sep":["Kharif","Whole year"],
                        "Oct":["Rabi","Whole year"],
                        "Nov":["Rabi","Whole year"],
                        "Dec":["Rabi","Whole year"]}
    dma = pd.DataFrame(columns=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],index=[district])
        
    for month in month_season_map.keys():
        dma.loc[district,month] = cga_bySea.loc[month_season_map[month],district.upper()].sum()
    dma.to_csv("data/dma.csv")
    return dma
                        
    
def main():
    """
    
    Args:
    district (str) - Full name of District
    
    Returns:
    a CSV file with the month wise AET in mm
    """
    district = sys.argv[1]
    aet = kcXpet(district)
    # print(aet)
    aetM3 = getCropsAET(district,aet)
    cga_bySea = calcDistSeasonArea(district)
    dma = calcDistMonthArea(district,cga_bySea)
    df = aetM3.divide(dma)
    df = df/10 # mm conversion
    df.to_csv("data/cwr.csv")


if __name__=="__main__":
    main()


