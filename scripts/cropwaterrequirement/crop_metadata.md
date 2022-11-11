# metadata
File: crop_db_corrected.csv

Last_update: 11-11-2022

Description: crop database file corrected for winter and autumn season

Time period: 2019-20

Spatial information: District level

District: 2011 Census

Script: cdb_correction.py

## Attributes:
district: column District names

area_ha: area of the crop in hectares

perc: percentage of crop area

## Additional information:
- **The "Winter" season from the original CSV changed to "Kharif" season**
- **The "Autumn" season from the original CSV changed to "Rabi" season**
- The crop of a season of a district in state, if any duplicate due to above change, combined and area of that crop in the season is aggregated by summation
- After the above summation, percentage of area for a crop in a season is calculated by the formula,
(area of the crop in a season of a district)/(total area of all the crops of that season of that district in a state)