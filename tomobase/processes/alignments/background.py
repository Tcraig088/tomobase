import numpy as np
from copy import deepcopy, copy
import napari
from scipy.ndimage import  binary_dilation
from skimage.filters import threshold_otsu

from tomobase.hooks import tomobase_hook_process
from tomobase.data import Sinogram
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
import PIL
from PIL import Image
import io

import ipywidgets as widgets
from IPython.display import display, clear_output
import stackview

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

_subcategories = {}
_subcategories[TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value()] = 'Background Corrections'
@tomobase_hook_process(name='Bin Data', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories=_subcategories)
def bin(sino:Sinogram, factor:int=2, inplace=True):
    """
    Bin a 3D or 4D array along the first two axes.

    Parameters:
    data (numpy.ndarray): Input array to be binned.
    factor (int): Binning factor.
    inplace (bool): Whether to modify the array in place or return a new array.

    Returns:
    numpy.ndarray: Binned array.
    """
    if not inplace:
        sino = deepcopy(sino)
    
    if sino.data.ndim == 3:
        # Bin the data for the first two axes
        sino.data = sino.data.reshape(sino.data.shape[0]//factor, factor, sino.data.shape[1]//factor, factor, sino.data.shape[2])
        sino.data = sino.data.mean(axis=1)
        sino.data = sino.data.mean(axis=2)
    elif sino.data.ndim == 4:
        # Bin the data for the first two axes
        sino.data = sino.data.reshape(sino.data.shape[0]//factor, factor, sino.data.shape[1]//factor, factor, sino.data.shape[2], sino.data.shape[3])
        sino.data = sino.data.mean(axis=1)
        sino.data = sino.data.mean(axis=2)
    else:
        raise ValueError("Input data must be a 3D or 4D array.")
    
    return sino


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



class ProcessingSinogramGui():
    def __init__(self, sino: Sinogram, size:int=256):
        self.sino = sino
        self.index = 0 
        self.size = 256


    def _on_slider_change(self, change):
        self.index = change.new
        #self.sinogram_widget.children = [self._group_widget, self._sinogram_item_view()]
        for widget in self.sinogram_widget.children[1].children:
            widget.children[1].slice_number = self.index

    def _sinogram_viewer(self):
        slider_widget = widgets.IntSlider(min=0, max=self.sino.data.shape[2]-1, value=self.index, description='Slice')
        angle_widget = widgets.Label(value='Angle: {}'.format(self.sino.angles[self.index]))
        self._group_widget = widgets.HBox([slider_widget, angle_widget])
        img_widget = self._sinogram_item_view()
        self.sinogram_widget = widgets.VBox([self._group_widget, img_widget])
        slider_widget.observe(self._on_slider_change, names='value')

        return self.sinogram_widget 
    
    def _sinogram_item_view(self):
        img_list = []
        for attr_name, attr_value in vars(self).items():
            if isinstance(attr_value, Sinogram):
                #img_data = deepcopy(attr_value.data).astype(np.float32)
                # img_data = ((img_data - img_data.min()) / (img_data.max() - img_data.min()))*255
                # img_data = img_data.astype(np.uint8)
                    
                # img = Image.fromarray(attr_value.data[:,:,self.index])
                # img = img.resize((self.size, self.size))
                # if img.mode == 'F':
                #     img = img.convert('L')
                # with io.BytesIO() as output:
                #     img.save(output, format="PNG")
                #     data = output.getvalue()
                img_data = attr_value._transpose_to_view(use_copy=True)
                img_widget = stackview.slice(img_data, slice_number=self.index)
                #img_widget = widgets.Image(value=data, format='png')
                label_widget = widgets.Label(value=attr_name)
                group_widget = widgets.VBox([label_widget, img_widget])
                
                img_list.append(group_widget)
        return widgets.HBox(img_list)


@tomobase_hook_process(name='Manual Masking', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories=_subcategories)
class MaskBackground(ProcessingSinogramGui):
    '''
    MaskBackground class to create a mask for the sinogram data.
    '''
    def __init__(self, 
                 sino: Sinogram, 
                 threshold: float = 0.0,
                 dilation: int = 0,
                 masking_radius: int = 0,
                 inplace: bool = True, 
                 size:int=256):
        '''
        Parameters
        ----------
        sino : Sinogram
            Sinogram data to be processed.'''
        
        super().__init__(sino, size)
        self.threshold = threshold
        self.dilation = dilation
        self.masking_radius = masking_radius
        self.inplace = inplace

        self.mask = deepcopy(self.sino)
        self._update_mask()
        self.show()
        
    def _update_mask(self):
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

        self.preview = deepcopy(self.sino)
        self.preview.data[~self.mask.data] = 0
    
    def _on_change(self, change):
        self.dilation = self.dilation_widget.value
        self.threshold = self.threshold_widget.value
        self.masking_radius = self.radius_widget.value
        self._update_mask()
        img_widget = self._sinogram_viewer()
        self.layout.children= [self.group_widget, img_widget, self.confirm_button]


    def _on_confirm(self, b):
        if not self.inplace:
            self.sino = deepcopy(self.sino)

        self._update_mask()
        self.sino.data[~self.mask.data] = 0
        return self.sino
    
    def show(self):
        radius_max_x = (self.sino.data.shape[0]-1) // 2
        radius_max_y = (self.sino.data.shape[1]-1) // 2
        if radius_max_x < radius_max_y:
            radius_max = radius_max_x
        else:
            radius_max = radius_max_y

        self.threshold_widget = widgets.FloatSlider(value=self.threshold, min=0, max=self.sino.data.max(), step=0.01, description='Threshold')
        self.dilation_widget = widgets.IntSlider(value=self.dilation, min=0, max=10, description='Dilation')
        self.radius_widget = widgets.IntSlider(value=self.masking_radius, min=0, max=radius_max, description='Masking Radius')
        self.group_widget = widgets.HBox([self.threshold_widget, self.dilation_widget, self.radius_widget])
        img_widget = self._sinogram_viewer()
        self.confirm_button = widgets.Button(description='Confirm')

        self.layout = widgets.VBox([self.group_widget, img_widget, self.confirm_button])

        self.threshold_widget.observe(self._on_change, names='value')
        self.dilation_widget.observe(self._on_change, names='value')
        self.radius_widget.observe(self._on_change, names='value')
        self.confirm_button.on_click(self._on_confirm)
        display(self.layout)


