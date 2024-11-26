import numpy as np
from copy import deepcopy
import napari
from scipy.ndimage import  binary_dilation
from skimage.filters import threshold_otsu

from tomobase.hooks import tomobase_hook_process
from tomobase.data import Sinogram
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES

import ipywidgets as widgets
from IPython.display import display, clear_output
import stackview

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

_subcategories = {}
_subcategories[TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value()] = 'Background Corrections'
@tomobase_hook_process(name='Subtract Median', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories=_subcategories)
def background_subtract_median(sino: Sinogram,  
              inplace:bool=True):
    """
    Subtract the median value of the sinogram from the sinogram data.
    
    Parameters
    ----------
    sino : Sinogram
        Sinogram data to be processed.
        inplace : bool, optional
        If True, the sinogram data will be updated in place.
        If False, a new sinogram will be returned.
        Default is True.
            
            Returns
            -------
            Sinogram
            Processed sinogram data.
            
            """
    if not inplace:
        sino = deepcopy(sino)

    median = np.median(sino.data)
    sino.data[sino.data<median] = 0

    return sino

@tomobase_hook_process(name='Manual Masking', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories=_subcategories)
class MaskBackground():
    def __init__(self, 
                 sino: Sinogram, 
                 threshold: float = 0.0,
                 dilation: int = 0,
                 masking_radius: int = 0,
                 inplace: bool = True):
        
        self.sino = sino
        self.threshold = threshold
        self.dilation = dilation
        self.masking_radius = masking_radius
        self.inplace = inplace
        
    def process(self):
        if self.threshold <= 0:
            threshold = threshold_otsu(self.sino.data)
        else:
            threshold = self.threshold
        
        self.mask.data = self.sino.data >= threshold
        
        if self.masking_radius > 0:
            z_dim = self.mask.data.shape[2]
            center_y, center_x, center_z = np.array(self.mask.data.shape) // 2
            y, x = np.ogrid[:self.mask.data.shape[0], :self.mask.data.shape[1]]
            distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            circular_mask = distance_from_center <= self.masking_radius
            cylindrical_mask = np.repeat(circular_mask[:, :, np.newaxis], z_dim, axis=2)
            self.mask.data = self.mask.data & cylindrical_mask
        
        if self.dilation > 0:
            self.mask.data = binary_dilation(self.mask.data, iterations=self.dilation)
    

    def view(self, bin=4):
        stackview.slice_by_slice(self.sino.data._bin(4)._transpose_to_view(), self.mask.data._bin(4)._transpose_to_view())
        
        
    def refresh(self):
        self.widgets
        stackview.slice_by_slice(self.sino.data._bin(4)._transpose_to_view(), self.mask.data._bin(4)._transpose_to_view())
        
        
    def generate(self) -> Sinogram:
        self.mask = deepcopy(self.sino)
        self.process()
        return self.mask
    
    def update(self):
        self.process()
        return self.mask
    
    def apply(self):
        if not self.inplace:
            self.sino = deepcopy(self.sino)
        
        self.sino.data[~self.mask.data] = 0
        return self.sino