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


def _create_projector(x, y, angles, use_gpu):
    proj_geom = astra.creators.create_proj_geom('parallel', 1, max(x, y), angles * np.pi / 180)
    vol_geom = astra.creators.create_vol_geom(y, x)
    if use_gpu:
        proj_id = astra.creators.create_projector('cuda', proj_geom, vol_geom)
    else:
        proj_id = astra.creators.create_projector('linear', proj_geom, vol_geom)
    return proj_id

