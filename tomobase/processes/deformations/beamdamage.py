import scipy.ndimage as ndimage
import skimage
import numpy as np
import copy
from tomobase.data import Volume
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.hooks import tomobase_hook_process

def _knockon(volume, knockon):
    kernel = np.ones((3, 3, 3))
    mask = (volume != 0).astype(int)
    pmask = ndimage.convolve(mask, kernel, mode='constant', cval=0.0)
    mask_interior = np.zeros(volume.shape, bool)
    mask_interior[pmask >= 27] = 1

    pmask = np.power(knockon, pmask/3)
    seed = np.random.rand(*volume.shape)
    
    print('sum:',np.sum(mask))
    print('knockonevents:', np.sum(mask[pmask > seed]))
    print('Buried :', np.sum(mask[mask_interior]))
    mask[pmask > seed] = 0
    mask[mask_interior] = 1
    volume = volume * mask

    return volume


def _deform(obj, deform, normalize=True):
    #something isnt quite right here the size keeps getting bigger 
    sig = 10
    coord = np.indices(obj.shape, dtype=np.float32)
    seed = (np.random.rand(3, *obj.shape) * 2) - 1
    seed_list = [skimage.filters.gaussian(seed[i], sig) for i in range(3)]
    amplitude = np.sqrt(sum(seed_list[i] ** 2 for i in range(3)))

    mask = (obj != 0).astype(int)
    count = np.sum(mask)

    for i in range(3):
        seed[i] = (seed[i] * deform) / amplitude
    coord = coord + seed
    obj = skimage.transform.warp(obj, coord)
    if normalize:
        obj_flat = obj.flatten()
        nonzero_indices = np.where(obj_flat != 0)[0]
        nonzero_values = obj_flat[nonzero_indices]
        sorted_indices = np.argsort(nonzero_values)
        if len(nonzero_values) <= count:
            threshold_value = np.min(nonzero_values)
        else:
            threshold_value = nonzero_values[sorted_indices[-count]]
        obj_flat[obj_flat < threshold_value] = 0
        obj = obj_flat.reshape(obj.shape)
        obj[obj>0] = 1

    return obj

@tomobase_hook_process(name='Beam Damage', category=TOMOBASE_TRANSFORM_CATEGORIES.DEFORM.value)
def beamdamage(volume: Volume, knockon: float = 0.01, elasticdeform=0.1, normalize: bool = True):
    volume.data = _deform(volume.data, elasticdeform, normalize)
    volume.data = _knockon(volume.data, knockon)
    return volume


