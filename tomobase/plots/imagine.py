import stackview
import ipywidgets as widgets
from IPython.display import display, clear_output
from tomobase.data import Sinogram

class Imagine():
    def __init__(self, *args, **kwargs):
        self._on_slider_change = self._on_slider_change

        self.display_width = kwargs.get('display_width', 800)
        self.display_height = kwargs.get('display_height', 800)

        max_slider_value = 0
        imgs=[]
        self.n_projections = []
        for sino in args:
            self.n_projections.append(sino.data.shape[2])
            if sino.data.shape[2] > max_slider_value:
                max_slider_value = sino.data.shape[2]
            imgs.append(sino.show(self.display_width, self.display_height, showdisplay=False))
                
        self._slider = widgets.IntSlider(min=0, max=max_slider_value, value=0, description='Projection')  
        self._slider.observe(self._on_slider_change, names='value')
        hbox=widgets.HBox(imgs)
        self.view = widgets.VBox([self._slider, hbox])
        display(self.view)
        
    def _on_slider_change(self, change):
        self._slider.value = change.new
        for i, item in enumerate(self.view.children[1].children):
            slider = item.children[0].children[0].children[0].children[1].children[0].children[0].children[1]
            if change.new < self.n_projections[i]:
                slider.value = change.new
            else:
                slider.value = self.n_projections[i]