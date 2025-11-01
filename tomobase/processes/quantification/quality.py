

from tomobase.data import Data
from tomobase.registrations.environment import proxy
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.hooks import tomobase_hook_process

_subcategory = ['Quality Evaluation']

@tomobase_hook_process(name='Structural Similarity',category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=_subcategory, isquantification=True)
def ssim( image:Data, reference:Data):
    if image.data.dtype == proxy.xupy.uint8:
        data_range = 255
    elif image.data.dtype == proxy.xupy.float32 or image.data.dtype == proxy.xupy.float64:
        data_range = 1.0
        if image.data.max() > 1.0:
            data_range = image.data.max() - image.data.min()
    value = proxy.skimage.metrics.structural_similarity(image.data, reference.data, data_range=data_range)
    return value

@tomobase_hook_process(name='Peak Signal to Noise',category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=_subcategory, isquantification=True)
def psnr(image:Data, reference:Data):
    if image.data.dtype == proxy.xupy.uint8:
        data_range = 255
    elif image.data.dtype == proxy.xupy.float32 or image.data.dtype == proxy.xupy.float64:
        data_range = 1.0
        if image.data.max() > 1.0:
            data_range = image.data.max() - image.data.min()
    value = proxy.skimage.metrics.peak_signal_noise_ratio(image.data, reference.data, data_range=data_range)
    return value

@tomobase_hook_process(name='Root Mean Squared Error', category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=_subcategory, isquantification=True)
def mse(image:Data, reference:Data):
    value = proxy.xupy.sqrt(proxy.skimage.metrics.mean_squared_error(image.data, reference.data)) * 100
    return value

@tomobase_hook_process(name='Mean Absolute Error',category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=_subcategory, isquantification=True)
def mae(image:Data, reference:Data):
    value = proxy.xupy.mean(proxy.xupy.abs(image.data - reference.data))*100
    return value

@tomobase_hook_process(name='Signal To Noise',category=TOMOBASE_TRANSFORM_CATEGORIES.QUANTIFICATION.value, subcategories=_subcategory, isquantification=True)
def snr(Image:Data):
    #Normalize Prior to Using
    value = 10*proxy.xupy.log10((proxy.xupy.mean(Image.data)**2)/(proxy.xupy.std(Image.data)**2))
    return value



