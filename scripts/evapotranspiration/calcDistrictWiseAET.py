"""
Calculates a districtwise AET using FAOs methodology
formula: AET = Kc*PET*Crop.Season.Group.Area
from which Crop Water Requirement and Irrigation Water Requirement are
calculated and exported to csv file for districts provided.
"""

import sys
from pathlib import Path
import pandas as pd

dataFol = Path.home().joinpath("Code", "atree", "scripts",
                               "evapotranspiration", "data")
petExcelFile = dataFol.joinpath("PET.csv")
cropGrAreaFile = dataFol.joinpath("CropGroups_Area.csv")
kcFile = dataFol.joinpath("Kc.csv")
effPreRef = dataFol.joinpath("PeRef.csv")
rainfall = dataFol.joinpath("rainfall.csv")

petDf = pd.read_csv(petExcelFile)
cAreaDf = pd.read_csv(cropGrAreaFile)
kcDf = pd.read_csv(kcFile).fillna(0)
effPreRefDf = pd.read_csv(effPreRef, index_col='Rainfall').fillna(0)
rainDf = pd.read_csv(rainfall).fillna(0)


def kcXpet(district):
    """generates Kc * PET values for the selected district

    Args:
        district (string): district name

    Returns:
        DataFrame: Kc*PET values for every month of the selected district
    """
    petDistrict = petDf[petDf['District'] == district]
    kcDf_val = kcDf.loc[:, "Jan":"Dec"].values
    petD_val = petDistrict.loc[:, "Jan":"Dec"].values
    kcXpet = pd.DataFrame(
        kcDf_val * petD_val, columns=kcDf.loc[:, "Jan":"Dec"].columns, index=kcDf["Groups_Season"])
    kcXpet['District'] = district
    # kcXpet.to_csv(dataFol.joinpath(district.lower()+'_aet.csv',index=True)
    return kcXpet


def getCropsAET(district, aet):
    """Kc * PET * Crop Area values in the selected district

    Args:
        district (string): district name
        aet (DataFrame): Kc * PET Dataframe

    Returns:
        DataFrame: Kc*PET*CropArea in m3
    """
    aetVal = aet.loc[:, "Jan":"Dec"].values * 10  # 10000/1000 (ha-mm to m3)
    cArea = cAreaDf[["Groups_Season", district.upper()]]
    cAreaVal = cArea.loc[:, district.upper()].values
    cAreaVal = cAreaVal.reshape(222, 1)
    aetM3 = pd.DataFrame(
        cAreaVal * aetVal, columns=aet.loc[:, "Jan":"Dec"].columns, index=cArea["Groups_Season"])
    # aetM3.to_csv(dataFol.joinpath(district.lower()+'_aetM3.csv', index=True)
    aetM3sum = aetM3.sum()
    # aetM3sum.to_csv(dataFol.joinpath(district.lower()+'_aetM3sum.csv', index=True)
    return aetM3sum


def calcDistSeasonArea(district):
    """Summation of Season wise crop area

    Args:
        district (string): district name

    Returns:
        DataFrame: Season wise Crop area
    """
    cga_bySea = cAreaDf.groupby("Season").sum()
    # cga_bySea.to_csv(dataFol.joinpath(district.lower()+'_cgaSea.csv')
    return cga_bySea


def calcDistMonthArea(district, cga_bySea):
    """month wise seasonal crop area

    Args:
        district (string): district name
        cga_bySea (DataFrame): Season Wise Crop area

    Returns:
        DataFrame: month wise seasonal crop area
    """
    month_season_map = {"Jan": ["Rabi", "Whole year"],
                        "Feb": ["Summer", "Whole year"],
                        "Mar": ["Summer", "Whole year"],
                        "Apr": ["Summer", "Whole year"],
                        "May": ["Summer", "Whole year"],
                        "Jun": ["Kharif", "Whole year"],
                        "Jul": ["Kharif", "Whole year"],
                        "Aug": ["Kharif", "Whole year"],
                        "Sep": ["Kharif", "Whole year"],
                        "Oct": ["Rabi", "Whole year"],
                        "Nov": ["Rabi", "Whole year"],
                        "Dec": ["Rabi", "Whole year"]}
    dma = pd.DataFrame(columns=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                       "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], index=[district])
    for month in month_season_map.keys():
        dma.loc[district, month] = cga_bySea.loc[month_season_map[month],
                                                 district.upper()].sum()
    # dma.to_csv(dataFol.joinpath(district.lower()+'_dma.csv')
    return dma


def effRain(district, cwr):
    """Calculate effective Precipitation for each month based on ET and P

    Args:
        district (string): district name
        cwr (DataFrame): month wise CWR for the district

    Returns:
        DataFrame: Effective rainfall month wise
    """
    selected = rainDf[rainDf['District'] == district].reset_index(drop=True)
    peDf = selected.copy(deep=True)
    peDf.drop(['State', 'Year'], inplace=True, axis=1)
    peDf.set_index("District", inplace=True)
    peDf.rename(index={district: 'Pe'}, inplace=True)
    peDf.index.name = None
    for month in selected.loc[:, "Jan":"Dec"].columns:
        rainVal = selected[month][0]
        if rainVal == 0:
            peDf[month]['Pe'] = 0
        else:
            etVal = cwr[month]['cwr']
            etCal = str(int((etVal//25)*25))
            peDf[month]['Pe'] = effPreRefDf[etCal][rainVal]
    return peDf


def main():
    """
    Calculates the Crop Water Requirement and Irrigation Water Requirement
    for the required district

    Usage:
    Python calcDistrictWiseAET.py [district]
    
    Args:
    district (str) - Full name of Districts seperated by comma
    (no whitespace inbetween)

    Returns:
    a CSV file with the month wise CWR and IWR in mm
    """
    print("started...")
    districts = sys.argv[1]
    # Check whether district names provided are available in PET csv
    # also capitalize the district names if not
    districts = (district.capitalize() for district in districts.split(
        ',') if district.capitalize() in petDf['District'].values)
    for district in districts:
        aet = kcXpet(district)
        aetM3 = getCropsAET(district, aet)
        cga_bySea = calcDistSeasonArea(district)
        dma = calcDistMonthArea(district, cga_bySea)
        cwr = aetM3.divide(dma)
        cwr = cwr/10  # mm conversion
        cwr.rename(index={district: 'cwr'}, inplace=True)
        eRain = effRain(district, cwr)
        df = cwr.append(eRain)
        df.loc['iwr'] = df.loc['cwr'] - df.loc['Pe']
        df.to_csv(dataFol.joinpath(district.lower()+'.csv'), index=True)
        print(district+' completed')


if __name__ == "__main__":
    main()
