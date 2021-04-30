# ROADMAP
> DEFINE STANDARD WellDataObj (path,metacols)
> Init Well Data Obj 
- define colnames: metacols,long,lat, state
- different read f() choices from csv,xls,shp
- CSV > GEODF (def make_gdf_from_df)
- define colnames: datacols
> PreProcess : in single step
- remove duplicates
- remove null rows
- remove duplicate geometries
> Get Elevation for all points [ONE-TIME]
> SJoins
  > Buffer geometries
> Visualize
- simple plot
> Save
- to shapefile
- to raster

> Loop following steps over 7 states  [TBD]
  > Subset a single state  [TBD]
    > Save to raster [TBD] (i/p: sdate,edate,elev)





