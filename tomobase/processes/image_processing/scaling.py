from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.registrations.environment import xp
from tomobase.data import Sinogram, Data, Volume
from tomobase.hooks import tomobase_hook_process

import ipywidgets as widgets
from IPython.display import display, clear_output
import stackview


_subcategories =['Image Scaling']
@tomobase_hook_process(name='Normalize', category=TOMOBASE_TRANSFORM_CATEGORIES.IMAGE_PROCESSING.value, subcategories=_subcategories)
def normalize(sino: Sinogram):
    """Normalize the sinogram data to the range [0, 1].
    
    Arguments:
        sino (Sinogram): The projection data
        inplace (bool): Whether to do the operation in-place in the input data object (default: True)
    Returns:
        Sinogram: The result
    """
    sino.data = (sino.data - xp.xupy.min(sino.data)) / (xp.xupy.max(sino.data) - xp.xupy.min(sino.data))
    return sino

@tomobase_hook_process(name='Bin Data', category=TOMOBASE_TRANSFORM_CATEGORIES.IMAGE_PROCESSING.value, subcategories=_subcategories)
def bin(obj: Data, factor: int = 2):
    """Bin the sinogram data by a specified factor.
    
    Arguments:
        sino (Sinogram): The projection data
        factor (int): The binning factor (default: 2)
        inplace (bool): Whether to do the operation in-place in the input data object (default: True)
    Returns:
        Sinogram: The result
    """
    skipped_axis = 0
    if isinstance(obj, Sinogram):
        skipped_axis += 1
    if obj.data.ndim > obj.dim_default:
        skipped_axis += 1

    axes = range(obj.data.ndim)
    factors = [1 if (i < skipped_axis) else factor for i in axes]


     # Check divisibility
    for i, (dim, b) in enumerate(zip(obj.data.shape, factors)):
        if dim % b != 0:
            raise ValueError(f"Axis {i} size {dim} not divisible by bin factor {b}")

    # Compute new shape for reshaping
    reshaped = []
    for dim, b in zip(obj.data.shape, factors):
        reshaped.extend([dim // b, b])
    obj.data = obj.data.reshape(reshaped)

    # Compute mean over binning axes
    for i in reversed(range(obj.data.ndim // 2)):
        obj.data = obj.data.mean(axis=i * 2 + 1) 

    if not obj.pixelsize == 1.0:
        obj.pixelsize = obj.pixelsize * factor
    
    return obj

@tomobase_hook_process(name='Pad Sinogram', category=TOMOBASE_TRANSFORM_CATEGORIES.IMAGE_PROCESSING.value, subcategories=_subcategories)
def pad_sinogram(sino: Sinogram, x: int = 0, y: int = 0):
    """ Pad the sinogram to the specified size.
    Arguments:
        sino (Sinogram): The projection data
        x (int): The target size for the x dimension
        y (int): The target size for the y dimension
        inplace (bool): Whether to do the operation in-place in the input data object (default: True)
    Returns:
        Sinogram: The result
    """
    pad_x = x - sino.data.shape[-2]
    pad_y = y - sino.data.shape[-1]
    if pad_x < 0 or pad_y < 0:
        raise ValueError("Cannot pad to a smaller size")
    sino.data = xp.xupy.pad(sino.data, ( (0, 0), (pad_x // 2, pad_x // 2), (pad_y // 2, pad_y // 2)), mode='constant')

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
    crop_x = sino.data.shape[-2] - x
    crop_y = sino.data.shape[-1] - y
    if crop_x < 0 or crop_y < 0:
        raise ValueError("Cannot crop to a smaller size")
    sino.data = sino.data[:, :, crop_x // 2:-crop_x // 2, crop_y // 2:-crop_y // 2]

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
        self.sino.data = Sinogram._transpose_from_view(self.view.crop())
        return self.sino