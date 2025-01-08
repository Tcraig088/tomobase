import numpy as np
from copy import deepcopy
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

def _bin(data, factor, inplace=True):
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
        data = deepcopy(data)
    
    if data.ndim == 3:
        # Bin the data for the first two axes
        data = data.reshape(data.shape[0]//factor, factor, data.shape[1]//factor, factor, data.shape[2])
        data = data.mean(axis=1)
        data = data.mean(axis=2)
    elif data.ndim == 4:
        # Bin the data for the first two axes
        data = data.reshape(data.shape[0]//factor, factor, data.shape[1]//factor, factor, data.shape[2], data.shape[3])
        data = data.mean(axis=1)
        data = data.mean(axis=2)
    else:
        raise ValueError("Input data must be a 3D or 4D array.")
    
    return data

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
                 inplace: bool = True, 
                 bin:int=4):
        
        self.sino = sino
        self.bin =bin
        self.threshold = threshold
        self.dilation = dilation
        self.masking_radius = masking_radius
        self.inplace = inplace
        
    def process(self, use_bin=True):
        print(self.threshold, self.dilation, self.masking_radius)
        self.sino_view.data += np.random.rand(*self.sino_view.data.shape)
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
        
        if use_bin:
            self.mask.data = _bin(self.mask.data, self.bin, inplace=False)


    def view(self):
        self.sino_view = deepcopy(self.sino)
        self.sino_view.data = _bin(self.sino.data, self.bin, inplace=False)




        self.generate()
        radius_max_x = (self.sino.data.shape[0]-1) // 2
        radius_max_y = (self.sino.data.shape[1]-1) // 2
        if radius_max_x < radius_max_y:
            radius_max = radius_max_x
        else:
            radius_max = radius_max_y

        threshold_widget = widgets.FloatSlider(value=self.threshold, min=0, max=self.sino.data.max(), step=0.01, description='Threshold')
        dilation_widget = widgets.IntSlider(value=self.dilation, min=0, max=10, description='Dilation')
        radius_widget = widgets.IntSlider(value=self.masking_radius, min=0, max=radius_max, description='Masking Radius')
        blank_widget = widgets.Label(value="")

        refresh_button = widgets.Button(description='Refresh')
        confirm_button = widgets.Button(description='Confirm')

        # Convert PIL images to ipywidgets.Image
        def pil_to_ipyimage(pil_image):
            # Convert the image to a supported mode
            if pil_image.mode == 'F':
                pil_image = pil_image.convert('L')
            with io.BytesIO() as output:
                pil_image.save(output, format="PNG")
                data = output.getvalue()
            return widgets.Image(value=data, format='png')

        image_widget = pil_to_ipyimage(Image.fromarray(self.sino_view.data[:,:,30]))
        mask_widget = pil_to_ipyimage(Image.fromarray(self.mask.data[:,:,30]))

        grid = widgets.GridBox(children=[image_widget, mask_widget, threshold_widget, dilation_widget, radius_widget, blank_widget, refresh_button, confirm_button], layout=widgets.Layout(grid_template_columns="repeat(2, 50%)"))

        # Display the grid
        display(grid)

        # if refresh button is clicked
        def on_refresh_button_clicked(b):
            self.threshold = threshold_widget.value
            self.dilation = dilation_widget.value
            self.masking_radius = radius_widget.value
            self.update()
            
            # Update the data in the widgets
            image_widget.value = pil_to_ipyimage(Image.fromarray(self.sino_view.data[:,:,30])).value
            mask_widget.value = pil_to_ipyimage(Image.fromarray(self.mask.data[:,:,30])).value
            
            # Reassign the widgets to the grid to force update
            grid.children = [image_widget, mask_widget, threshold_widget, dilation_widget, radius_widget, blank_widget, refresh_button, confirm_button]

        # if confirm button is clicked
        def on_confirm_button_clicked(b):
            self.threshold = threshold_widget.value
            self.dilation = dilation_widget.value
            self.masking_radius = radius_widget.value
            self.apply()

        # Connect the buttons to their handlers
        refresh_button.on_click(on_refresh_button_clicked)
        confirm_button.on_click(on_confirm_button_clicked)

    def generate(self) -> Sinogram:
        self.mask = deepcopy(self.sino)
        self.process()
        return self.mask
    
    def update(self):
        self.process()
        print('updated')
        return self.mask
    
    def apply(self):
        if not self.inplace:
            self.sino = deepcopy(self.sino)

        self.process(use_bin=False)
        self.sino.data[~self.mask.data] = 0
        return self.sino