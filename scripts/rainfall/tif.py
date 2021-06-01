from rasterio.transform import Affine


def get_params():
    return {
        'rain' : {'height':129,'width':135,'affine':Affine(0.25, 0, 66.375, 0, -0.25, 38.625) },
        'tmin' : {'height':31,'width':31,'affine':Affine(1, 0, 67, 0, -1, 38) },
        'tmax' : {'height':31,'width':31,'affine':Affine(1, 0, 67, 0, -1, 38) }
    }