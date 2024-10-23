import numpy as np
from copy import deepcopy
import napari
from scipy.ndimage import rotate
from skimage.util import random_noise

from scipy.ndimage import center_of_mass, rotate
from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

_subcategories = {}
_subcategories[TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value()] = 'Background Corrections'
@tomobase_hook_process(name='Subtract Median', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories=_subcategories)
def background_subtract_median(sino,  
              inplace:bool=True):

    if not inplace:
        sino = deepcopy(sino)

    median = np.median(sino.data)
    sino.data[sino.data<median] = 0

    return sino

@tomobase_hook_process(name='Subtract Manual', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories=_subcategories)
def background_subtract_manual(sino,  
              inplace:bool=True):

    if not inplace:
        sino = deepcopy(sino)

    median = np.median(sino.data)
    sino.data[sino.data<median] = 0

    return sino