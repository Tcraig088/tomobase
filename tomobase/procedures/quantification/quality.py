

from tomobase.data import Image
from tomobase.core.environment import proxy
from ...core.registers.categories import categories
from tomobase.core.bootstraps import process_hook


subcategory = categories.add_category('Quality Metrics', value=9, inheritor = 'Analyze')

@process_hook(name='Structural Similarity',category=categories['Quality Metrics'])
def ssim( image:Image, reference:Image):
    if image.data.dtype == proxy.xupy.uint8:
        data_range = 255
    elif image.data.dtype == proxy.xupy.float32 or image.data.dtype == proxy.xupy.float64:
        data_range = 1.0
        if image.data.max() > 1.0:
            data_range = image.data.max() - image.data.min()
    value = proxy.skimage.metrics.structural_similarity(image.data, reference.data, data_range=data_range)
    return value

@process_hook(name='Peak Signal to Noise',category=categories['Quality Metrics'])
def psnr(image:Image, reference:Image):
    if image.data.dtype == proxy.xupy.uint8:
        data_range = 255
    elif image.data.dtype == proxy.xupy.float32 or image.data.dtype == proxy.xupy.float64:
        data_range = 1.0
        if image.data.max() > 1.0:
            data_range = image.data.max() - image.data.min()
    value = proxy.skimage.metrics.peak_signal_noise_ratio(image.data, reference.data, data_range=data_range)
    return value

@process_hook(name='Root Mean Squared Error', category=categories['Quality Metrics'])
def mse(image:Image, reference:Image):
    value = proxy.xupy.sqrt(proxy.skimage.metrics.mean_squared_error(image.data, reference.data)) * 100
    return value

@process_hook(name='Mean Absolute Error',category=categories['Quality Metrics'])
def mae(image:Image, reference:Image):
    value = proxy.xupy.mean(proxy.xupy.abs(image.data - reference.data))*100
    return value

@process_hook(name='Signal To Noise',category=categories['Quality Metrics'])
def snr(Image:Image):
    #Normalize Prior to Using
    value = 10*proxy.xupy.log10((proxy.xupy.mean(Image.data)**2)/(proxy.xupy.std(Image.data)**2))
    return value



