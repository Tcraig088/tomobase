
from tomobase.data import Volume
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.environment import xp

def _knockon(volume, knockon):
    kernel = xp.xupy.ones((3, 3, 3))
    mask = (volume != 0).astype(int)
    pmask = xp.scipy.ndimage.convolve(mask, kernel, mode='constant', cval=0.0)
    mask_interior = (pmask >= 27)

    pmask = xp.xupy.power(knockon, pmask/3)
    seed = xp.xupy.random.rand(*volume.shape)
    
    mask[pmask > seed] = 0
    mask[mask_interior] = 1
    volume = volume * mask

    return volume


def _deform(obj, deform, normalize=True):
    #something isnt quite right here the size keeps getting bigger 
    sig = 10
    coord = xp.xupy.indices(obj.shape, dtype= xp.xupy.float32)
    seed = (xp.xupy.random.rand(3, *obj.shape) * 2) - 1
    seed_list = [xp.scipy.ndimage.gaussian_filter(seed[i], sig) for i in range(3)]
    amplitude = xp.xupy.sqrt(sum(seed_list[i] ** 2 for i in range(3)))

    mask = (obj != 0).astype(int)
    count = xp.xupy.sum(mask)

    for i in range(3):
        seed[i] = (seed[i] * deform) / amplitude
    coord = coord + seed
    obj = xp.scipy.ndimage.map_coordinates(obj, coord, order=1, mode='constant', cval=0.0)
    if normalize:
        obj_flat = obj.flatten()
        nonzero_indices = xp.xupy.where(obj_flat != 0)[0]
        nonzero_values = obj_flat[nonzero_indices]
        sorted_indices = xp.xupy.argsort(nonzero_values)
        if len(nonzero_values) <= count:
            threshold_value = xp.xupy.min(nonzero_values)
        else:
            threshold_value = nonzero_values[sorted_indices[-count]]
        obj_flat[obj_flat < threshold_value] = 0
        obj = obj_flat.reshape(obj.shape)
        obj[obj>0] = 1

    return obj

@tomobase_hook_process(name='Beam Damage', category=TOMOBASE_TRANSFORM_CATEGORIES.DEFORM.value)
def beamdamage(volume: Volume, knock_on: float = 0.01, elastic_deform:float=0.1, normalize:bool=True):
    volume.data = _deform(volume.data, elastic_deform, normalize)
    volume.data = _knockon(volume.data, knock_on)
    return volume


