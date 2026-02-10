
from ...data import Volume
from ...registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from ...hooks import process_hook
from ...registrations.environment import proxy

from magicgui.tqdm import tqdm

def _knockon(volume, knockon):
    kernel = proxy.xupy.ones((3, 3, 3))
    mask = (volume != 0).astype(int)
    pmask = proxy.scipy.ndimage.convolve(mask, kernel, mode='constant', cval=0.0)
    mask_interior = (pmask >= 27)

    pmask = proxy.xupy.power(knockon, pmask/3)
    seed = proxy.xupy.random.rand(*volume.shape)
    
    mask[pmask > seed] = 0
    mask[mask_interior] = 1
    volume = volume * mask

    return volume


def _deform(obj, deform, normalize=True):
    #something isnt quite right here the size keeps getting bigger 
    sig = 10
    coord = proxy.xupy.indices(obj.shape, dtype= proxy.xupy.float32)
    seed = (proxy.xupy.random.rand(3, *obj.shape) * 2) - 1
    seed_list = [proxy.scipy.ndimage.gaussian_filter(seed[i], sig) for i in range(3)]
    amplitude = proxy.xupy.sqrt(sum(seed_list[i] ** 2 for i in range(3)))

    mask = (obj != 0).astype(int)
    count = proxy.xupy.sum(mask)

    for i in range(3):
        seed[i] = (seed[i] * deform) / amplitude
    coord = coord + seed
    obj = proxy.scipy.ndimage.map_coordinates(obj, coord, order=1, mode='constant', cval=0.0)
    
    if normalize:
        obj_flat = obj.flatten()
        nonzero_indices = proxy.xupy.where(obj_flat != 0)[0]
        nonzero_values = obj_flat[nonzero_indices]
        sorted_indices = proxy.xupy.argsort(nonzero_values)
        if len(nonzero_values) <= count:
            threshold_value = proxy.xupy.min(nonzero_values)
        else:
            threshold_value = nonzero_values[sorted_indices[-count]]
        obj_flat[obj_flat < threshold_value] = 0
        obj = obj_flat.reshape(obj.shape)
        obj[obj>0] = 1

    return obj

@process_hook(name='Beam Damage', category=TOMOBASE_TRANSFORM_CATEGORIES.DEFORM.value)
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
    
    volume.data = _deform(volume.data, elastic_deform, normalize)
    volume.data = _knockon(volume.data, knock_on)
    return volume


