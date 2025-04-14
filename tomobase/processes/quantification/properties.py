from tomobase.data import Data, Volume
from tomobase.registrations.environment import xp
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.hooks import tomobase_hook_process

subcategory = ['Phyiscal Properties']
@tomobase_hook_process(name='Surface Area', category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=subcategory, isquantification=True)
def surface_area(volume: Volume, threshold: float = 0.0, ):
    if xp.xupy.isclose(threshold, 0.0):
        threshold = xp.skimage.filters.threshold_otsu(volume.data)
    mask = xp.xupy.zeros_like(volume.data)
    mask[volume.data > threshold] = 1

    kernel = xp.xupy.ones((3, 3, 3))
    mask= xp.scipy.ndimage.convolve(mask, kernel, mode='constant', cval=0.0)/27
    mask[mask == 1] = 0
    mask[mask > 0] = 1
    value = xp.xupy.sum(mask) * volume.pixelsize**2
    return value

@tomobase_hook_process(name='Volume', category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=subcategory, isquantification=True)
def volume(volume: Volume, threshold: float = 0.0):
    if xp.xupy.isclose(threshold, 0.0):
        threshold = xp.skimage.filters.threshold_otsu(volume.data)
    mask = xp.xupy.zeros_like(volume.data)
    mask[volume.data > threshold] = 1
    value = xp.xupy.sum(mask) * volume.pixelsize**3
    return value

@tomobase_hook_process(name='Surface Area Volume Ratio', category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=subcategory, isquantification=True)
def sav(volume: Volume, threshold: float = 0.0):
    if xp.xupy.isclose(threshold, 0.0):
        threshold = xp.skimage.filters.threshold_otsu(volume.data)
    sa = surface_area(volume, threshold)
    vol = volume(volume, threshold)
    value = sa / vol
    return value

@tomobase_hook_process(name='Alloying', category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=subcategory, isquantification=True)
def alloying(volume: Volume, reference:Volume, materiala:float=0.0, materialb:float=0.0, std_homogenized:float=0.0):
    """Calculate the alloying of two materials in a volume.
    Args:
        volume (Volume): The input volume.
        materiala (float): The first material value.
        materialb (float): The second material value.
    Returns:
        float: The alloying value.
    """
    std_reference = xp.xupy.std(reference.data)
    if xp.xupy.isclose(std_homogenized, 0.0) and xp.xupy.isclose(std_reference, 0.0):
        materiala_count = reference.data[xp.xupy.isclose(reference.data, materiala)].count()
        materiala_sum = reference.data[xp.xupy.isclose(reference.data, materiala)].sum()

        materialb_count = reference.data[xp.xupy.isclose(reference.data, materialb)].count()
        materialb_sum = reference.data[xp.xupy.isclose(reference.data, materialb)].sum()

    
        homogenized_data = xp.xupy.zeros_like(reference.data)
        homogenized_data[reference.data>0] = 1.0
        homogenized_data *= (materiala_sum + materialb_sum)/(materiala_count + materialb_count)

        std_homogenized = xp.xupy.std(homogenized_data)
    std_volume = xp.xupy.std(volume.data)
    value = (std_volume - std_reference)/(std_homogenized - std_reference)
    return value