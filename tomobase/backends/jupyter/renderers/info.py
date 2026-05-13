from PIL import Image as PILImage
import numpy as np
import io
import itertools

from IPython.display import display
from ipywidgets import VBox, HBox, Accordion, Label, Output, Image, IntSlider, ToggleButtons
import pyvista as pv

from ....core import base_classes
from .components import build_accordion
from .slice import ImageSliceWidget, SliceInfoWidget
from .volume import ImageVolumeWidget, VolumeInfoWidget

     
class InfoWidgetAbstract(VBox):
    def __init__(self, image: base_classes.ImageAbstract, **kwargs):
        super().__init__(**kwargs)
        name_widget = Label(value=f"Sample: {image.name}")
        process_widget = Label(value=f"Process: {image.process_name}")
        pixel_size_widget = Label(value=f"Pixel Size (nm): {image.pixel_size}")

        _data_info_widget = {
            "Dimensions": str(image.xr.dims),
            "Shape": str(image.xr.shape),
            "Data Type": str(image.xr.dtype),
            "Max Value": str(image.values.max()),
            "Min Value": str(image.values.min()),
        }
        data_info_widget = build_accordion(_data_info_widget, title="Data Info")
        metadata_widget = build_accordion(image.metadata, title="Metadata")
        
        self.children = (name_widget, process_widget, pixel_size_widget, data_info_widget, metadata_widget)
    
@base_classes.ImageAbstract.ipywidgets.register(name="info")
class InfoWidget(HBox):
    def __init__(self, image: base_classes.ImageAbstract, **kwargs):
        super().__init__(**kwargs)
        self.info_widget = InfoWidgetAbstract(image)
        display_type = kwargs.pop("display_type", "slice")
        if display_type == "slice":
            self.image_widget = ImageSliceWidget(image)
            self.slice_info_widget = SliceInfoWidget(image, self.image_widget)
            vbox = VBox([self.info_widget, self.slice_info_widget])
            self.children = (self.image_widget, vbox)
        elif display_type == "volume":
            self.image_widget = ImageVolumeWidget(image)
            self.slice_info_widget = SliceInfoWidget(image, self.image_widget)
            self.volume_info_widget = VolumeInfoWidget(self.image_widget)
            vbox = VBox([self.info_widget, self.slice_info_widget, self.volume_info_widget])
            self.children = (self.image_widget, vbox)