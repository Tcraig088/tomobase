from IPython import display
from ipywidgets import VBox, HBox, Button, Layout
import pyvista as pv

from ....core import data_classes

class VolumeRenderer:
    def __init__(self, vol: data_classes.Volume, verbose=True):
        self.vol = vol

    
    
    
    plotter = pv.Plotter()
    plotter.add_volume(vol.values, **kwargs)
    plotter.show()
    
    
def show_volume(vol: data_classes.Volume, verbose=True):
    renderer = VolumeRenderer(vol, verbose=verbose)
    return renderer