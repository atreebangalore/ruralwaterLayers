# -*- coding: utf-8 -*-
"""
Created on Sat Apr  9 11:42:28 2022

@author: rashmi
"""

import os
import csv
import glob
import numpy as np
import pandas as pd
from pandas import DataFrame, read_excel, merge
from pandas import DataFrame
# specify your path of directory
path = r"F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture"
print(path)
# call listdir() method
# path is a directory of which you want to list
directories = os.listdir( path )
print(directories)


#files to join
PET = pd.read_excel('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/PET.xlsx')
CropGroupArea = pd.read_excel('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/CropGroups_Area.xlsx')
CropGroupKc = pd.read_excel('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/ETCrop.xlsx')
Season=pd.read_excel('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/Seasons_Summary.xlsx')



CropGroupKc1 = CropGroupKc.merge(CropGroupArea[["Groups_Season", "ARIYALUR"]])
CropGroupKc3.head()

#Add blank colummns
CropGroupKc1["Jan"]=""
CropGroupKc1["Feb"]=""
CropGroupKc1["Mar"]=""
CropGroupKc1["Apr"]=""
CropGroupKc1["May"]=""
CropGroupKc1["Jun"]=""
CropGroupKc1["Jul"]=""
CropGroupKc1["Aug"]=""
CropGroupKc1["Sep"]=""
CropGroupKc1["Oct"]=""
CropGroupKc1["Nov"]=""
CropGroupKc1["Dec"]=""

#Replaceall blancks with Nan
#Replace Nan with values from PET file district wise
CropGroupKc1 = CropGroupKc1.replace(r'^s*$', np.nan, regex=True)
CropGroupKc2=CropGroupKc1.fillna(PET.loc[PET['District'] == 'Ariyalur'])
print(CropGroupKc2)
CropGroupKc3=CropGroupKc2.fillna(method='ffill')

#Correct next line check for left /right)
CropGroupKc3.rename(columns={'Jan': 'JanET','Feb': 'FebET','Mar': 'MarET','Apr': 'AprET','May': 'MayET','Jun': 'JunET','Jul': 'JulET','Aug': 'AugET','Sep': 'SepET','Oct': 'OctET','Nov': 'NovET','Dec': 'DecET'}, inplace=True)
CropGroupKc4=CropGroupKc3.merge(CropGroupKc[["Groups_Season","Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]],how='outer')
print(CropGroupKc4)
print(PET)


#calculate AET (KcxPET mm)
CropGroupKc4["JanAET"]=CropGroupKc4['JanET']*CropGroupKc4['Jan']*CropGroupKc4['ARIYALUR']
CropGroupKc4["FebAET"]=CropGroupKc4['FebET']*CropGroupKc4['Feb']*CropGroupKc4['ARIYALUR']
CropGroupKc4["MarAET"]=CropGroupKc4['MarET']*CropGroupKc4['Mar']*CropGroupKc4['ARIYALUR']
CropGroupKc4["AprAET"]=CropGroupKc4['AprET']*CropGroupKc4['Apr']*CropGroupKc4['ARIYALUR']
CropGroupKc4["MayAET"]=CropGroupKc4['MayET']*CropGroupKc4['May']*CropGroupKc4['ARIYALUR']
CropGroupKc4["JunAET"]=CropGroupKc4['JunET']*CropGroupKc4['Jun']*CropGroupKc4['ARIYALUR']
CropGroupKc4["JulAET"]=CropGroupKc4['JulET']*CropGroupKc4['Jul']*CropGroupKc4['ARIYALUR']
CropGroupKc4["AugAET"]=CropGroupKc4['AugET']*CropGroupKc4['Aug']*CropGroupKc4['ARIYALUR']
CropGroupKc4["SepAET"]=CropGroupKc4['SepET']*CropGroupKc4['Sep']*CropGroupKc4['ARIYALUR']
CropGroupKc4["OctAET"]=CropGroupKc4['OctET']*CropGroupKc4['Oct']*CropGroupKc4['ARIYALUR']
CropGroupKc4["NovAET"]=CropGroupKc4['NovET']*CropGroupKc4['Nov']*CropGroupKc4['ARIYALUR']
CropGroupKc4["DecAET"]=CropGroupKc4['DecET']*CropGroupKc4['Dec']*CropGroupKc4['ARIYALUR']

#Total AETmm
CropGroupKc4.loc['Sum'] = CropGroupKc4.sum(axis=0)

CropGroupKc5= CropGroupKc4[246:247] # selecting only the row with total AET
CropGroupKc6 = CropGroupKc5.iloc[:,28:42]*10 #converting to m3
print(CropGroupKc5)

#add extra columns to be able to join
CropGroupKc6.insert (0, "Join","0")
CropGroupKc6.insert (1, "District","0")
CropGroupKc6.insert (2, "Season","0")

#Add seasonal data
#put seasonal area vallues based on month in the excel
CropGroupKc7 = CropGroupKc6.append(Season[Season['District'] == 'ARIYALUR'], sort=False)
CropGroupKc7.loc['TotalArea'] = CropGroupKc7[1:6].sum(axis=0)

#select only values 
CropGroupKc8=CropGroupKc7.iloc[[0,6],3:15] 

CropGroupKc8=CropGroupKc7.iloc[[0],3:15] 
print(CropGroupKc4)


print(CropGroupET7)
CropGroupKc8.to_csv('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/Output2.csv',index = False)
CropGroupKc7.to_csv('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/Output.csv',index = False)

##########################################

#Rainfall
#files to join
Rainfall = pd.read_excel('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/Rainfall.xlsx')
EffRainfall = pd.read_excel('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/EffRainfall.xlsx')
EffRainfall_2 = pd.read_excel('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/EffRainfall_2.xlsx')

print(EffRainfall)
lookup rainfall from eff rainfall 
if CWR = eff rainfall table:
    
column_names=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
EffRain=pd.DataFrame(columns=column_names)


#try iloc row position , column position https://www.youtube.com/watch?v=qUMdvhXYNfg



filter1= Rainfall['January']==EffRainfall['Rainfall']

EffRainfall.apply(df.isin(),axis='1')
new=CropGroupKc8.iloc[0]
New1=EffRainfall_2.iloc[0].isin(new)


df[df.Name.isin(['Alice', 'Bob'])]
filter2=CropGroupKc8.iloc[1]==EffRainfall.iloc[0]
filter2=CropGroupET6.iloc[1].map(EffRainfall_2)


New1.to_csv('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/Output.csv',index = False)

other = pd.DataFrame({filter1,filter2})  #https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.isin.html
df.isin(other)

print(CropGroupET6)

np.where(Rainfall['Jan'] =, df['Budget'] * 0.78125, df['Budget'])

CropGroupKc.to_csv('F:/ATREE/Pacific Institute/Ganga/Water Quantity/Agriculture/Output2.csv',index = False)

  
#ifcolumn name= Ariyalur copy zET values from row
["JanET","FebET","MarET","AprET","MayET","JunET","JulET","AugET","SepET","OctET","NovET","DecET"]