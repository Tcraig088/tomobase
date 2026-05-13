
from ....core.data_classes.images import Sinogram
from ....core import registers, proxy, base_classes

subcategory = registers.categories.add_hierarchy('Scaling', value=6, parent = 'Image Processing')
@registers.procedures.register(name='Normalize', category=subcategory)
def normalize(image: base_classes.ImageAbstract):
    """Normalize the sinogram data to the range [0, 1].
    
    Args:
        image (ImageAbstract): The input image data

    Returns:
        ImageAbstract: The result

    """
    if "signals" in image.xr.dims:
        for i in range(image.xr.sizes['signals']):
            sl = image.xr.isel(signals=i)
            image.xr.loc[dict(signals=sl.coords["signals"].item())] = (sl - sl.min()) / (sl.max() - sl.min())
    else:
        image.xr = (image.xr - image.xr.min()) / (image.xr.max() - image.xr.min())
    return image

@registers.procedures.register(name='Bin Data', category=subcategory)
def bin(image: base_classes.ImageAbstract, factor: int = 2):
    """Bin the image data by a specified factor.

    Args:
        image (ImageAbstract): The input image data
        factor (int): The binning factor (default: 2)

    Returns:
        ImageAbstract: The result
    """

    factors = [1 if dim in image.non_spatial_dims else factor for dim in image.xr.dims]
    for i, (dim, b) in enumerate(zip(image.xr.shape, factors)):
        if dim % b != 0:
            raise ValueError(f"Axis {i} size {dim} not divisible by bin factor {b}")


    reshaped = []
    for dim, b in zip(image.xr.shape, factors):
        reshaped.extend([dim // b, b])
    data = image.xr.data.reshape(reshaped)
    bin_axes = tuple(range(1, 2 * len(factors), 2))
    data = data.mean(axis=bin_axes)

    image.reshape_and_fill(data)
    if not image.pixel_size == 1.0:
        image.pixel_size = image.pixel_size * factor
    
    return image

@registers.procedures.register(name='Pad Sinogram', category=subcategory)
def pad_sinogram(sino: Sinogram, x: int = 0, y: int = 0):
    #TODO Fix
    """ Pad the sinogram to the specified size.

    Args:
        sino (Sinogram): The projection data
        x (int): The target size for the x dimension
        y (int): The target size for the y dimension

    Returns:
        Sinogram: The result
    """
    
    pad_x = x - sino.xr.shape[-2]
    pad_y = y - sino.xr.shape[-1]
    if pad_x < 0 or pad_y < 0:
        raise ValueError("Cannot pad to a smaller size")
    sino.xr = proxy.xupy.pad(sino.xr, ( (0, 0), (pad_x // 2, pad_x // 2), (pad_y // 2, pad_y // 2)), mode='constant')

    return sino

#@tomobase_hook_process(name='Crop Sinogram', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def crop_sinogram(sino: Sinogram, x: int = 0, y: int = 0):
    """
    Crop the sinogram to the specified size.

    Parameters:
    sino (Sinogram): Input sinogram to be cropped.
    x (int): Target size for the x dimension.
    y (int): Target size for the y dimension.
    inplace (bool): Whether to modify the array in place or return a new array.

    Returns:
    Sinogram: Cropped sinogram.
    """
    crop_x = sino.xr.shape[-2] - x
    crop_y = sino.xr.shape[-1] - y
    if crop_x < 0 or crop_y < 0:
        raise ValueError("Cannot crop to a smaller size")
    sino.xr = sino.xr[:, :, crop_x // 2:-crop_x // 2, crop_y // 2:-crop_y // 2]

    return sino

#@tomobase_hook_process(name='Crop', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories = _subcategories)
class CropSinogram:
    def __init__(self, sino:Sinogram):
        self.sino = sino
        self._view()
    
    def _view(self):
        self.view = stackview.crop(self.sino._transpose_to_view())
        confirm = widgets.Button(description='Confirm')
        confirm.on_click(self.on_confirm)
        display(widgets.VBox([self.view, confirm]))

    def on_confirm(self, b):
        self.sino.xr = Sinogram._transpose_from_view(self.view.crop())
        return self.sino