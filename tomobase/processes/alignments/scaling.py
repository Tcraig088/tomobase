from copy import deepcopy, copy
import numpy as np
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.registrations.environment import xp
from tomobase.data import Sinogram
from tomobase.hooks import tomobase_hook_process
import ipywidgets as widgets
from IPython.display import display, clear_output
import stackview

_subcategories = {}
_subcategories[TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value] = 'Image Scaling'

@tomobase_hook_process(name='Normalize', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def normalize(sino: Sinogram, inplace: bool = True):
    """Normalize the sinogram data to the range [0, 1].
    
    Arguments:
        sino (Sinogram): The projection data
        inplace (bool): Whether to do the operation in-place in the input data object (default: True)
    Returns:
        Sinogram: The result
    """
    
    if not inplace:
        sino = deepcopy(sino)
    sino.set_context()
    
    sino.data = (sino.data - np.min(sino.data)) / (np.max(sino.data) - np.min(sino.data))
    return sino

@tomobase_hook_process(name='Bin Data', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def bin(sino: Sinogram, factor: int = 2, inplace: bool = True):
    """Bin the sinogram data by a specified factor.
    
    Arguments:
        sino (Sinogram): The projection data
        factor (int): The binning factor (default: 2)
        inplace (bool): Whether to do the operation in-place in the input data object (default: True)
    Returns:
        Sinogram: The result
    """
    if not inplace:
        sino = deepcopy(sino)
    sino.set_context()
    
    if sino.data.ndim == 3:
        # Bin the data for the last two axes
        sino.data = sino.data.reshape(sino.data.shape[0], sino.data.shape[1] // factor, factor, sino.data.shape[2] // factor, factor)
        sino.data = sino.data.mean(axis=2)
        sino.data = sino.data.mean(axis=3)
    elif sino.data.ndim == 4:
        # Bin the data for the last two axes
        sino.data = sino.data.reshape(sino.data.shape[0], sino.data.shape[1], sino.data.shape[2] // factor, factor, sino.data.shape[3] // factor, factor)
        sino.data = sino.data.mean(axis=3)
        sino.data = sino.data.mean(axis=4)
    else:
        raise ValueError("Input data must be a 3D or 4D array.")
    
    if not sino.pixelsize == 1.0:
        sino.pixelsize = sino.pixelsize * factor
    
    return sino

@tomobase_hook_process(name='Pad Sinogram', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def pad_sinogram(sino: Sinogram, x: int = 0, y: int = 0, inplace: bool = True):
    """ Pad the sinogram to the specified size.
    Arguments:
        sino (Sinogram): The projection data
        x (int): The target size for the x dimension
        y (int): The target size for the y dimension
        inplace (bool): Whether to do the operation in-place in the input data object (default: True)
    Returns:
        Sinogram: The result
    """
    if not inplace:
        sino = deepcopy(sino)

    pad_x = x - sino.data.shape[-2]
    pad_y = y - sino.data.shape[-1]
    if pad_x < 0 or pad_y < 0:
        raise ValueError("Cannot pad to a smaller size")
    sino.data = xp.pad(sino.data, ( (0, 0), (pad_x // 2, pad_x // 2), (pad_y // 2, pad_y // 2)), mode='constant')

    return sino

#@tomobase_hook_process(name='Crop Sinogram', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def crop_sinogram(sino: Sinogram, x: int = 0, y: int = 0, inplace: bool = True):
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
    if not inplace:
        sino = deepcopy(sino)

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