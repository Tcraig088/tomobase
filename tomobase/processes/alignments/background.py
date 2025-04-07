import numpy as np
from copy import deepcopy, copy
import napari
from scipy.ndimage import  binary_dilation
from skimage.filters import threshold_otsu

from tomobase.hooks import tomobase_hook_process
from tomobase.data import Sinogram
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.registrations.environment import xp, GPUContext
import PIL
from PIL import Image
import io

import ipywidgets as widgets
from IPython.display import display, clear_output
import stackview

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

_subcategories = {}
_subcategories[TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value] = 'Background Corrections'
@tomobase_hook_process(name='Subtract Median', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def background_subtract_median(sino: Sinogram,  inplace:bool=True):
    """Subtract the median of the sinogram from the sinogram."
    Args:
        sino (Sinogram): The sinogram to process
        inplace (bool): Whether to do the processing in-place in the input data object
    Returns:
        Sinogram (Sinogram): The resulting Sinogram
    """
    if not inplace:
        sino = deepcopy(sino)

    sino.set_context()
    median = xp.median(sino.data)
    sino.data[sino.data<median] = 0

    return sino


class MaskBackgroundManual():
    def __init__(self, sino: Sinogram, inplace: bool = True):
        self.sino = sino
        self.threshold = 0.0
        self.dilation = 0
        self.masking_radius = 0.0
        self.inplace = inplace
        self.preview = False

        self.mask = deepcopy(self.sino)
        self._view()

    def _update_mask(self):
        if self.threshold <= 0:
            threshold = threshold_otsu(self.data)
        else:
            threshold = self.threshold

        self.mask[:,:,:] = (self.data >= threshold)

        if self.masking_radius > 0:
            z_dim = self.mask.shape[0]
            center_z, center_x, center_y = np.array(self.mask.shape) // 2
            y, x = np.ogrid[:self.mask.shape[2], :self.mask.shape[1]]
            distance_from_center = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            circular_mask = distance_from_center <= self.masking_radius
            cylindrical_mask = np.repeat(circular_mask[np.newaxis, :, :], z_dim, axis=0)
            self.mask[:,:,:] = (self.mask & cylindrical_mask)

        if self.dilation > 0:
            self.mask[:,:,:] = binary_dilation(self.mask, iterations=self.dilation)

        self.mask[:,:,:] = self.mask*255
        if self.preview:
            self.temp_mask = copy(self.mask)
            self.mask[:,:,:] = self.data 
            self.mask[~self.temp_mask] = 0

    def _view(self):
        self.data = self.sino._transpose_to_view()
        self.mask = np.zeros_like(self.data, dtype=bool)
        self._update_mask()
        radius_max_x = (self.data.shape[2]-1) // 2
        radius_max_y = (self.data.shape[1]-1) // 2
        if radius_max_x < radius_max_y:
            radius_max = radius_max_x
        else:
            radius_max = radius_max_y
 
        self.view = stackview.curtain(self.data, self.mask)
        self.preview_tickbox = widgets.Checkbox(value=False, description='Preview') 
        self.threshold_widget = widgets.FloatSlider(value=self.threshold, min=0, max=self.data.max(), step=0.01, description='Threshold')
        self.dilation_widget = widgets.IntSlider(value=self.dilation, min=0, max=30, description='Dilation')
        self.masking_radius_widget = widgets.FloatSlider(value=self.masking_radius, min=0, max=radius_max, description='Masking Radius')
        self.confirm_button = widgets.Button(description='Confirm')

        self.preview_tickbox.observe(self._on_change_preview, names='value')
        self.threshold_widget.observe(self._on_change_threshold, names='value')
        self.dilation_widget.observe(self._on_change_dilation, names='value')
        self.masking_radius_widget.observe(self._on_change_masking_radius, names='value')
        self.confirm_button.on_click(self._on_confirm)

        display(widgets.VBox([self.preview_tickbox, self.threshold_widget, self.dilation_widget, self.masking_radius_widget, self.view, self.confirm_button]))

    def _on_change_preview(self, change):   
        self.preview = change.new
        self._update_mask()
        self.view.update()

    def _on_change_threshold(self, change):
        self.threshold = change.new
        self._update_mask()
        self.view.update()

    def _on_change_dilation(self, change):
        self.dilation =  change.new
        self._update_mask()
        self.view.update()
    
    def _on_change_masking_radius(self, change):
        self.masking_radius = change.new
        self._update_mask()
        self.view.update()

    def _on_confirm(self, b):
        if not self.inplace:
            self.sino = deepcopy(self.sino)

        self._update_mask()
        self.data[~self.mask] = 0
        self.sino.data = Sinogram._transpose_from_view(self.data)
        return self.sino
