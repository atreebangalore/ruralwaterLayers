from typing import List
import ee
ee.Initialize()


def mask_clouds(image: ee.Image) -> ee.Image:
    scored = ee.Algorithms.Landsat.simpleCloudScore(image)
    return image.updateMask(scored.select(['cloud']).lt(20))


def add_quality_bands(image: ee.Image) -> ee.Image:
    ndvi = image.normalizedDifference(['B5', 'B4']).rename(['ndvi'])
    mndwi = image.normalizedDifference(['B3', 'B6']).rename(['mndwi'])
    ndbi = image.normalizedDifference(['B6', 'B5']).rename(['ndbi'])
    di = (image.normalizedDifference(['B6', 'B5'])).subtract(
        image.normalizedDifference(['B5', 'B4'])).rename(['DI'])
    return mask_clouds(image).addBands(ndvi).addBands(mndwi).addBands(
        ndbi).addBands(di).addBands(image.metadata('system:time_start'))


def get_q_mosaic(col: ee.ImageCollection, param: str, bands: List[str], area: ee.FeatureCollection) -> ee.Image:
    return col.qualityMosaic(param).select(
        bands).reproject('EPSG:4326', None, 30).clipToCollection(area)


def vector_reducer(image: ee.Image, geometry: ee.Geometry) -> ee.FeatureCollection:
    return image.reduceToVectors(
        reducer=ee.Reducer.countEvery(),
        geometry=geometry,
        scale=30,
        maxPixels=1e10
    )


def rand_pts(vector: ee.FeatureCollection) -> ee.FeatureCollection:
    return ee.FeatureCollection.randomPoints(
        region=vector,
        points=100,
        seed=1234,
        maxError=1
    )


def main() -> None:
    start_date = '2020-06-01'
    end_date = '2021-05-31'
    landsat = ee.ImageCollection('LANDSAT/LC08/C01/T1_TOA').filterDate(
        start_date, end_date).map(add_quality_bands)
    jrc_urban = ee.Image("JRC/GHSL/P2016/BUILT_LDSMT_GLOBE_V1").select('built')
    bands = ['B3', 'B4', 'B5', 'B6', 'ndvi', 'mndwi', 'ndbi', 'DI', 'BQA']

    ndvi_quality = get_q_mosaic(landsat, 'ndvi', bands, area)
    ndbi_quality = get_q_mosaic(landsat, 'DI', bands, area)
    mndwi_quality = get_q_mosaic(landsat, 'mndwi', bands, area)

    agri_ndvi = ((ndvi_quality.select('ndvi')).gt(0.54)).And(
        (ndbi_quality.select('ndvi')).gt(0.35))
    other_ndbi = ((ndbi_quality.select('DI')).gt(-0.08)
                    ).And((ndvi_quality.select('mndwi')).lt(-0.2))
    urban_ndvi = ((ndvi_quality.select('DI')).lt(-0.0799)).And((
        ndvi_quality.select('DI')).gt(-0.6599)).And((ndvi_quality.select('ndvi')).lt(0.445)).And(
            (ndvi_quality.select('ndvi')).gt(0))
    water_mndwi = ((mndwi_quality.select('mndwi')).gt(0.48)).And(
        (mndwi_quality.select('ndvi')).lt(-0.01))

    agri_only = agri_ndvi.updateMask(agri_ndvi).clipToCollection(
        area).reproject('EPSG:4326', None, 30)
    other_only = other_ndbi.updateMask(other_ndbi).clipToCollection(
        area).reproject('EPSG:4326', None, 30)
    urban_only = urban_ndvi.updateMask(urban_ndvi).clipToCollection(
        area).reproject('EPSG:4326', None, 30)
    water_only = water_mndwi.updateMask(water_mndwi).clipToCollection(
        area).reproject('EPSG:4326', None, 30)

    agri_vec = vector_reducer(agri_only, karnataka.geometry())
    other_vec = vector_reducer(other_only.And(
        jrc_urban.remap([1, 2], [1, 1])), karnataka.geometry())
    urban_vec = vector_reducer(urban_only.And(
        jrc_urban.remap([5, 6], [1, 1])), karnataka.geometry())
    water_vec = vector_reducer(water_only, karnataka.geometry())

    agri_signatures = rand_pts(agri_vec)
    other_signatures = rand_pts(other_vec)
    urban_signatures = rand_pts(urban_vec)
    water_signatures = rand_pts(water_vec)
