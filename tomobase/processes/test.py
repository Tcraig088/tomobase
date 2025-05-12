import numpy as np
from copy import deepcopy, copy
import napari
from scipy.ndimage import  binary_dilation
from skimage.filters import threshold_otsu

from magicgui.tqdm import trange
from tomobase.data import Data
from tomobase.hooks import tomobase_hook_process
from tomobase.data import Sinogram, Image
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.registrations.environment import xp, GPUContext

import time
from typing import Union


from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

_subcategories = ['Background Corrections']
#@tomobase_test_process(category=TOMOBASE_TRANSFORM_CATEGORIES.IMAGE_PROCESSING.value, subcategories=_subcategories)
def test_process(image: Data, value: float = 0.0):
    """Subtract the median of the sinogram from the sinogram."
    Args:
        sino (Sinogram): The sinogram to process
        inplace (bool): Whether to do the processing in-place in the input data object
    Returns:
        Sinogram (Sinogram): The resulting Sinogram
    """
    for _i in trange(30):
        time.sleep(1)
    median = xp.xupy.median(image.data)
    image.data[image.data<median] = 0

    return image