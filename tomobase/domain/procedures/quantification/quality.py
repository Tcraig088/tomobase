

from ....core import registers, proxy, base_classes



subcategory = registers.categories.add_hierarchy('Quality Metrics', value=9, parent = 'Analyze')

@registers.procedures.register(name='Structural Similarity',category=registers.categories['Quality Metrics'])
def ssim( image:base_classes.ImageAbstract, reference:base_classes.ImageAbstract):
    if image.xr.dtype == proxy.xupy.uint8:
        data_range = 255
    elif image.xr.dtype == proxy.xupy.float32 or image.xr.dtype == proxy.xupy.float64:
        data_range = 1.0
        if image.xr.max() > 1.0:
            data_range = image.xr.max() - image.xr.min()
    value = proxy.skimage.metrics.structural_similarity(image.xr, reference.xr, data_range=data_range)
    return value

@registers.procedures.register(name='Peak Signal to Noise',category=registers.categories['Quality Metrics'])
def psnr(image:base_classes.ImageAbstract, reference:base_classes.ImageAbstract):
    if image.xr.dtype == proxy.xupy.uint8:
        data_range = 255
    elif image.xr.dtype == proxy.xupy.float32 or image.xr.dtype == proxy.xupy.float64:
        data_range = 1.0
        if image.xr.max() > 1.0:
            data_range = image.xr.max() - image.xr.min()
    value = proxy.skimage.metrics.peak_signal_noise_ratio(image.xr, reference.xr, data_range=data_range)
    return value

@registers.procedures.register(name='Root Mean Squared Error', category=registers.categories['Quality Metrics'])
def mse(image:base_classes.ImageAbstract, reference:base_classes.ImageAbstract):
    value = proxy.xupy.sqrt(proxy.skimage.metrics.mean_squared_error(image.xr, reference.xr)) * 100
    return value

@registers.procedures.register(name='Mean Absolute Error',category=registers.categories['Quality Metrics'])
def mae(image:base_classes.ImageAbstract, reference:base_classes.ImageAbstract):
    value = proxy.xupy.mean(proxy.xupy.abs(image.xr - reference.xr))*100
    return value

@registers.procedures.register(name='Signal To Noise',category=registers.categories['Quality Metrics'])
def snr(image:base_classes.ImageAbstract):
    #Normalize Prior to Using
    value = 10*proxy.xupy.log10((proxy.xupy.mean(Image.data)**2)/(proxy.xupy.std(Image.data)**2))
    return value



