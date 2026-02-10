from tomobase.data import BaseImageModel, Volume
from tomobase.registrations.environment import proxy
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.hooks import process_hook

subcategory = ['Phyiscal Properties']
@process_hook(name='Surface Area', category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=subcategory, isquantification=True)
def surface_area(volume: Volume, threshold: float = 0.0, ):
    if proxy.xupy.isclose(threshold, 0.0):
        threshold = proxy.skimage.filters.threshold_otsu(volume.data)
    mask = proxy.xupy.zeros_like(volume.data)
    mask[volume.data > threshold] = 1

    kernel = proxy.xupy.ones((3, 3, 3))
    mask= proxy.scipy.ndimage.convolve(mask, kernel, mode='constant', cval=0.0)/27
    mask[mask == 1] = 0
    mask[mask > 0] = 1
    value = proxy.xupy.sum(mask) * volume.pixelsize**2
    return value

@process_hook(name='Volume', category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=subcategory, isquantification=True)
def volume(volume: Volume, threshold: float = 0.0):
    if proxy.xupy.isclose(threshold, 0.0):
        threshold = proxy.skimage.filters.threshold_otsu(volume.data)
    mask = proxy.xupy.zeros_like(volume.data)
    mask[volume.data > threshold] = 1
    value = proxy.xupy.sum(mask) * volume.pixelsize**3
    return value

@process_hook(name='Surface Area Volume Ratio', category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=subcategory, isquantification=True)
def sav(volume: Volume, threshold: float = 0.0):
    if proxy.xupy.isclose(threshold, 0.0):
        threshold = proxy.skimage.filters.threshold_otsu(volume.data)
    sa = surface_area(volume, threshold)
    vol = volume(volume, threshold)
    value = sa / vol
    return value

@process_hook(name='Alloying', category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=subcategory, isquantification=True)
def alloying(volume: Volume, reference:Volume, materiala:float=0.0, materialb:float=0.0, std_homogenized:float=0.0):
    """Calculate the alloying of two materials in a volume.
    Args:
        volume (Volume): The input volume.
        materiala (float): The first material value.
        materialb (float): The second material value.
    Returns:
        float: The alloying value.
    """
    std_reference = proxy.xupy.std(reference.data)
    if proxy.xupy.isclose(std_homogenized, 0.0) and proxy.xupy.isclose(std_reference, 0.0):
        materiala_count = reference.data[proxy.xupy.isclose(reference.data, materiala)].count()
        materiala_sum = reference.data[proxy.xupy.isclose(reference.data, materiala)].sum()

        materialb_count = reference.data[proxy.xupy.isclose(reference.data, materialb)].count()
        materialb_sum = reference.data[proxy.xupy.isclose(reference.data, materialb)].sum()

    
        homogenized_data = proxy.xupy.zeros_like(reference.data)
        homogenized_data[reference.data>0] = 1.0
        homogenized_data *= (materiala_sum + materialb_sum)/(materiala_count + materialb_count)

        std_homogenized = proxy.xupy.std(homogenized_data)
    std_volume = proxy.xupy.std(volume.data)
    value = (std_volume - std_reference)/(std_homogenized - std_reference)
    return value