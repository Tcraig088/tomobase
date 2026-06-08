
from ....core.data_classes.images import Volume
from ....core import registers, logger, progress, utils, GPUContext, get_xp

def _knockon(volume, knockon, xp=None, ndimage=None):
    kernel = xp.ones((3, 3, 3))
    mask = (volume != 0).astype(int)
    pmask = ndimage.convolve(mask, kernel, mode='constant', cval=0.0)
    mask_interior = (pmask >= 27)

    pmask = xp.power(knockon, pmask/3)
    seed = xp.random.rand(*volume.shape)
    
    mask[pmask > seed] = 0
    mask[mask_interior] = 1
    volume = volume * mask

    return volume


def _deform(obj, deform, normalize=True, xp=None, ndimage=None):
    sig = 10
    coord = xp.indices(obj.shape, dtype= xp.float32)
    seed = (xp.random.rand(3, *obj.shape) * 2) - 1
    seed_list = [ndimage.gaussian_filter(seed[i], sig) for i in range(3)]
    amplitude = xp.sqrt(sum(seed_list[i] ** 2 for i in range(3)))

    mask = (obj != 0).astype(int)
    count = xp.sum(mask)

    for i in range(3):
        seed[i] = (seed_list[i] * deform) / amplitude
    coord = coord + seed
    obj = ndimage.map_coordinates(obj, coord, order=1, mode='constant', cval=0.0)
    
    if normalize:
        obj_flat = obj.flatten()
        nonzero_indices = xp.where(obj_flat != 0)[0]
        nonzero_values = obj_flat[nonzero_indices]
        sorted_indices = xp.argsort(nonzero_values)
        if len(nonzero_values) <= count:
            threshold_value = xp.min(nonzero_values)
        else:
            threshold_value = nonzero_values[sorted_indices[-count]]
        obj_flat[obj_flat < threshold_value] = 0
        obj = obj_flat.reshape(obj.shape)
        obj[obj>0] = 1

    return obj

@registers.procedures.register(name='Beam Damage', category=registers.categories['Deform'])
def beamdamage(volume: Volume, knock_on: float = 0.01, elastic_deform:float=0.1, normalize:bool=True):
    """Apply beam damage simulation to a volume.

    Args:
        volume (Volume): The input volume to be deformed.
        knock_on (float, optional): The knock-on effect strength. Defaults to 0.01.
        elastic_deform (float, optional): The elastic deformation strength. Defaults to 0.1.
        normalize (bool, optional): Whether to normalize the output. Defaults to True.

    Returns:
        Volume: The deformed volume.
    """
    
    xp = get_xp(volume.data)
    ndimage = utils.get_module('ndimage', volume.context)
    
    data = volume.xr.data
    data = xp.asarray(data)
    
    data = _deform(data, elastic_deform, normalize, xp=xp, ndimage=ndimage)
    data = _knockon(data, knock_on, xp=xp, ndimage=ndimage)
    
    volume.xr.data = data
    return volume


