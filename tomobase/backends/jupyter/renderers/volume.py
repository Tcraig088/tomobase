from IPython import display
from ipywidgets import VBox, HBox, Accordion, Label, Output
import pyvista as pv

from ....core import data_classes

class VolumeRenderer:
    def __init__(self, vol: data_classes.images.Volume, verbose=True, **kwargs):
        pv.set_jupyter_backend("trame")
        kwargs["cmap"] = kwargs.get("cmap", "cividis")
        kwargs["opacity"] = kwargs.get("opacity", "foreground")
        kwargs["shade"] = kwargs.get("shade", True)


        self.vol = vol
        self.vol_display = pv.Plotter()

        self.vol_display.add_volume(vol.values, **kwargs)
        self.vol_output = Output()
        self.verbose = verbose

        with self.vol_output:
            self.vol_display.show()

        name_widget = Label(value=f"Sample: {vol.name}")
        process_widget = Label(value=f"Process: {vol.process_name}")
        pixel_size_widget = Label(value=f"Pixel Size (nm): {vol.pixel_size}")

        _data_info_widget = {
            "Dimensions": str(vol.data.dims),
            "Shape": str(vol.data.shape),
            "Data Type": str(vol.data.dtype),
            "Max Value": str(vol.values.max()),
            "Min Value": str(vol.values.min()),
        }
        data_info_widget = self.build_accordion(_data_info_widget, title="Data Info")
        metadata_widget = self.build_accordion(vol.metadata, title="Metadata")
        
        self.info_widget = VBox([name_widget, process_widget, pixel_size_widget, data_info_widget, metadata_widget])
    
    def build_accordion(self, _dict, title=""):
        children = []
        for key, value in _dict.items():
            if isinstance(value, dict):
                children.append(self.build_accordion(value, key))
            else:
                children.append(HBox([Label(value=f"{key}:"), Label(value=f"{value}")]))
        vb = VBox(children)
        accordion = Accordion(children=[vb])
        accordion.set_title(0, title)

        return accordion

    @classmethod
    def show(cls, vol,verbose, **kwargs):
        obj = cls(vol, verbose, **kwargs)
        if obj.verbose:
            display.display(HBox([obj.vol_output, obj.info_widget]))
        else:
            display.display(obj.vol_output)

    @classmethod
    def construct(cls, vol, verbose=True, **kwargs):
        return cls(vol, verbose, **kwargs)

print("done stuff")
data_classes.images.Volume.renderer = VolumeRenderer