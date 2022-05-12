"""
Calculates a districtwise AET using FAOs methodology
formula: AET = Kc*PET*Crop.Season.Group.Area
from which Crop Water Requirement and Irrigation Water Requirement are
calculated and exported to a csv file.
If district names provided are provided as argument, it would calculate and
export csv for each district, if not it would calculate and export for all names
under District Heading and also export a combine allDistrict.csv
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
cropHeading = "Groups_Season"


def clean_dataframe(df, filePath):
    """checks for the district heading with the possible district heading list
    and keeps only the district and months columns while dropping out all other
    unrelated columns, if district heading could not be found then stops the 
    script execution.

    Args:
        df (DataFrame): input dataframe to check for district column
        filePath (string): just to include path in sys.exit()

    Returns:
        DataFrame: Cleaned DataFrame
    """
    possible_district_headings = []
    h_variations = ['district', 'district name', 'district_name',
                    'districtName', 'district_n', 'd_n']
    for label in h_variations:
        possible_district_headings.append(label.lower())
        possible_district_headings.append(label.upper())
        possible_district_headings.append(label.capitalize())
        possible_district_headings.append(label.title())
    try:
        district_heading = list(
            set(possible_district_headings) & set(df.columns))[0]
    except:
        sys.exit(filePath+'\n'+"Could not find District Column")
    heading_list = [district_heading]+list(df.loc[:, "Jan":"Dec"].columns)
    diff = list(set(df.columns).difference(heading_list))
    if len(diff) != 0:
        df.drop(diff, inplace=True, axis=1)
    df.rename(columns={district_heading: 'DISTRICT'}, inplace=True)
    df['DISTRICT'] = df['DISTRICT'].str.upper()
    return df


# read csv and checks for the proper headings
petDf = pd.read_csv(petExcelFile)
petDf = clean_dataframe(petDf, str(petExcelFile))

cAreaDf = pd.read_csv(cropGrAreaFile)
if cropHeading not in cAreaDf.columns:
    sys.exit(str(cropGrAreaFile)+'\n'+"Could not find Crops Column")

kcDf = pd.read_csv(kcFile)
if cropHeading not in kcDf.columns:
    sys.exit(str(kcFile)+'\n'+"Could not find Crops Column")

effPreRefDf = pd.read_csv(effPreRef, index_col='Rainfall')

rainDf = pd.read_csv(rainfall)
rainDf = clean_dataframe(rainDf, str(rainfall))


def kcXpet(district):
    """generates Kc * PET values for the selected district

    Args:
        district (string): district name

    Returns:
        DataFrame: Kc*PET values for every month of the selected district
    """
    petDistrict = petDf[petDf['DISTRICT'] == district]
    kcDf_val = kcDf.loc[:, "Jan":"Dec"].values
    petD_val = petDistrict.loc[:, "Jan":"Dec"].values
    kcXpet = pd.DataFrame(
        kcDf_val * petD_val, columns=kcDf.loc[:, "Jan":"Dec"].columns, index=kcDf[cropHeading])
    kcXpet['DISTRICT'] = district
    # kcXpet.to_csv(dataFol.joinpath(district.lower()+'_aet.csv'),index=True)
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
    cArea = cAreaDf[[cropHeading, district]]
    cAreaVal = cArea.loc[:, district].values
    cAreaVal = cAreaVal.reshape(222, 1)
    aetM3 = pd.DataFrame(
        cAreaVal * aetVal, columns=aet.loc[:, "Jan":"Dec"].columns, index=cArea[cropHeading])
    #aetM3.to_csv(dataFol.joinpath(district.lower()+'_aetM3.csv'), index=True)
    aetM3sum = aetM3.sum()
    #aetM3sum.to_csv(dataFol.joinpath(district.lower()+'_aetM3sum.csv'), index=True)
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
                                                 district].sum()
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
    selected = rainDf[rainDf['DISTRICT'] == district].reset_index(drop=True)
    peDf = selected.copy(deep=True)
    peDf.set_index('DISTRICT', inplace=True)
    indexName = f'{district}_Pe'
    peDf.rename(index={district: indexName}, inplace=True)
    peDf.index.name = None
    for month in selected.loc[:, "Jan":"Dec"].columns:
        rainVal = selected[month][0]
        if rainVal == 0:
            peDf[month][indexName] = 0
        else:
            etVal = cwr[month][f'{district}_cwr']
            if etVal < 25:
                peDf[month][indexName] = 0
            else:
                try:
                    etCal = str(int((etVal//25)*25))
                    peDf[month][indexName] = effPreRefDf[etCal][rainVal]
                except:
                    peDf[month][indexName] = 0
    return peDf


def checkDf(district, xStatus):
    """Checks the input Dataframe for Duplicate records for each District

    Args:
        district (string): District name to check duplication
        xStatus (string): Status of execution for printing purpose

    Returns:
        string: xStatus string to print
    """
    petDistrict = petDf[petDf['DISTRICT'] == district]
    petIndex = len(petDistrict.index)
    rainDistrict = rainDf[rainDf["DISTRICT"] == district]
    rainIndex = len(rainDistrict.index)
    cAreaDistrict = cAreaDf[[cropHeading, district]]
    cAreaIndex = len(cAreaDistrict.columns)
    if petIndex > 1 or rainIndex > 1 or cAreaIndex > 2:
        return f'failed - duplicate records found'
    else:
        return xStatus


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
    # overAllStatus - status message to print at the end of execution
    overAllStatus = 'Execution Successful'
    try:
        districts = sys.argv[1]
        districts1 = [district.upper() for district in districts.split(',')]
        # get only district names available in PET csv
        districts = list(set(districts1) & set(petDf['DISTRICT'].values))
        # provided names that dont match with PET csv
        leftOut = list(set(districts) ^ set(districts1))
        print('Identified Districts:\n', districts)
    except:
        # if no argument provided grab intersecting district names from csv files
        districts1 = list(set(petDf['DISTRICT'].values) & set(cAreaDf.columns))
        districts = list(set(districts1) & set(rainDf["DISTRICT"].values))
        # district names which are not present in all csv files
        leftOut = list(set(petDf['DISTRICT'].values) ^ set(cAreaDf.columns))
        leftOut = leftOut + list(set(districts1) ^
                                 set(rainDf["DISTRICT"].values))
        print('Identified Districts:\n', districts)
    df = pd.DataFrame()
    for district in districts:
        print(district, end=' ')
        xStatus = 'completed'
        # Check for duplicate District names in DataFrames
        xStatus = checkDf(district, xStatus)
        if xStatus != 'completed':
            print(f'-> {xStatus}')
            overAllStatus = 'Some Operations Failed!'
            continue
        # Calculation
        aet = kcXpet(district)
        aetM3 = getCropsAET(district, aet)
        cga_bySea = calcDistSeasonArea(district)
        dma = calcDistMonthArea(district, cga_bySea)
        cwr = aetM3.divide(dma)
        cwr = cwr/10  # mm conversion
        cwr.rename(index={district: f'{district}_cwr'}, inplace=True)
        eRain = effRain(district, cwr)
        cwr = cwr.append(eRain)
        try:
            cwr.loc[f'{district}_iwr'] = cwr.loc[f'{district}_cwr'] - \
                cwr.loc[f'{district}_Pe']
            cwr.loc[f'{district}_iwr(m3)'] = (
                cwr.loc[f'{district}_iwr']*dma.loc[district]) * 10  # mm conversion
        except:
            if xStatus == 'completed':
                xStatus = 'failed iwr calculation'
            overAllStatus = 'Some Operations Failed!'
        cwr.to_csv(dataFol.joinpath(f'{district}.csv'), index=True)
        df = df.append(cwr)
        print(f'-> {xStatus}')
    if len(districts) > 1:
        df.to_csv(dataFol.joinpath('allDistrict.csv'), index=True)
    if leftOut != []:
        print('\nLeft Out Districts :', leftOut, '', sep='\n')
    print(overAllStatus)


if __name__ == "__main__":
    main()
