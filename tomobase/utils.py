import astra
import numpy as np


def _circle_mask(n):
    y, x = np.meshgrid(np.linspace(-1, 1, n), np.linspace(-1, 1, n))
    return x ** 2 + y ** 2 <= 1

def _get_default_iterations(method):
    if 'em' in method.lower():
        return 15
    elif 'sirt' in method.lower() or 'sart' in method.lower():
        return 150
    elif 'art' in method.lower():
        return 10_000
    else:
        return 1


def _create_projector(array, angles, use_gpu):
    if array.ndim == 2:
        return _create_projector_2d(array.shape[0], array.shape[2], angles, use_gpu)
    elif array.ndim == 3:
        return _create_projector_3d(array.shape[2], array.shape[1], array.shape[0], angles, use_gpu)
    else:
        raise ValueError("Array must be either 2D or 3D")
    
def _create_projector_3d(x, y, z, angles, use_gpu):
    print('Creating projector with geometry (x, y, z, n):', x, y, z, angles.shape[0])
    proj_geom = astra.creators.create_proj_geom('parallel3d', 1, 1,  y, x, angles * np.pi / 180)
    vol_geom = astra.creators.create_vol_geom(y,x,z)
    if use_gpu:
        proj_id = astra.creators.create_projector('cuda3d', proj_geom, vol_geom)
    else:
        proj_id = astra.creators.create_projector('linear3d', proj_geom, vol_geom)
    return proj_id


def _create_projector_2d(x, z, angles, use_gpu):
    proj_geom = astra.creators.create_proj_geom('parallel', 1, max(x, z), angles * np.pi / 180)
    vol_geom = astra.creators.create_vol_geom(z,x)
    if use_gpu:
        proj_id = astra.creators.create_projector('cuda', proj_geom, vol_geom)
    else:
        proj_id = astra.creators.create_projector('linear', proj_geom, vol_geom)
    return proj_id
