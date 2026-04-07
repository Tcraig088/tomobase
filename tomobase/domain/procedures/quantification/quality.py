

from ....core import registers, proxy, base_classes



subcategory = registers.categories.add_category('Quality Metrics', value=9, inheritor = 'Analyze')

@registers.procedures.register(name='Structural Similarity',category=registers.categories['Quality Metrics'])
def ssim( image:base_classes.ImageAbstract, reference:base_classes.ImageAbstract):
    if image.data.dtype == proxy.xupy.uint8:
        data_range = 255
    elif image.data.dtype == proxy.xupy.float32 or image.data.dtype == proxy.xupy.float64:
        data_range = 1.0
        if image.data.max() > 1.0:
            data_range = image.data.max() - image.data.min()
    value = proxy.skimage.metrics.structural_similarity(image.data, reference.data, data_range=data_range)
    return value

@registers.procedures.register(name='Peak Signal to Noise',category=registers.categories['Quality Metrics'])
def psnr(image:base_classes.ImageAbstract, reference:base_classes.ImageAbstract):
    if image.data.dtype == proxy.xupy.uint8:
        data_range = 255
    elif image.data.dtype == proxy.xupy.float32 or image.data.dtype == proxy.xupy.float64:
        data_range = 1.0
        if image.data.max() > 1.0:
            data_range = image.data.max() - image.data.min()
    value = proxy.skimage.metrics.peak_signal_noise_ratio(image.data, reference.data, data_range=data_range)
    return value

@registers.procedures.register(name='Root Mean Squared Error', category=registers.categories['Quality Metrics'])
def mse(image:base_classes.ImageAbstract, reference:base_classes.ImageAbstract):
    value = proxy.xupy.sqrt(proxy.skimage.metrics.mean_squared_error(image.data, reference.data)) * 100
    return value

@registers.procedures.register(name='Mean Absolute Error',category=registers.categories['Quality Metrics'])
def mae(image:base_classes.ImageAbstract, reference:base_classes.ImageAbstract):
    value = proxy.xupy.mean(proxy.xupy.abs(image.data - reference.data))*100
    return value

@registers.procedures.register(name='Signal To Noise',category=registers.categories['Quality Metrics'])
def snr(image:base_classes.ImageAbstract):
    #Normalize Prior to Using
    value = 10*proxy.xupy.log10((proxy.xupy.mean(Image.data)**2)/(proxy.xupy.std(Image.data)**2))
    return value



