from abc import ABCMeta, abstractmethod
from tomobase.data import Volume, Sinogram
import ipywidgets as widgets
from IPython.display import display, clear_output

import stackview
import inspect

class ProcessGui():
    def __init__(self):
        pass
    
    def view(self, bin=4):
        self.generate()
        
        sinos = []
        volumes = []
        widgets_list = []
        label_list = []
        
        signature = inspect.signature(self.__init__)
        for name, param in signature.parameters.items():
            if name != 'self':
                if param.annotation == Sinogram:
                    self.sino = Sinogram.from_data_tuple(self.sino)
                    sinos.append(self.sino)
                elif param.annotation == Volume:
                    self.vol = Volume.from_data_tuple(self.vol)
                    volumes.append(self.vol)
                elif param.annotation == int:
                    widget = widgets.IntSlider(param.default, min=-10000, max=10000)
                    label_list.append(widgets.Label(name))
                    widgets_list.append(widget)
                    widget.observe(lambda change: self.update_widget(name, change.new), names='value')
                elif param.annotation == float:
                    widget = widgets.FloatSlider(param.default, min=-10000, max=10000)
                    label_list.append(widgets.Label(name))
                    widgets_list.append(widget)
                    widget.observe(lambda change: self.update_widget(name, change.new), names='value')
                elif param.annotation == bool:
                    widget = widgets.Checkbox(param.default)
                    label_list.append(widgets.Label(name))
                    widgets_list.append(widget)
                    widget.observe(lambda change: self.update_widget(name, change.new), names='value')
                elif param.annotation == str:
                    widget = widgets.Text(param.default)
                    label_list.append(widgets.Label(name))
                    widgets_list.append(widget)
                    widget.observe(lambda change: self.update_widget(name, change.new), names='value')
                else:
                    raise ValueError(f'Parameter {name} not supported')

        if len(sinos) > 0 and len(volumes) > 0:
            raise ValueError('Only one Sinogram or Volume is allowed')
        
        data_list = []
        if len(sinos) > 0:
            for item in sinos:
                data_list.append(item._transpose_to_view(data=item._bin(copy=True, factor=bin)))
            image_viewer = stackview.side_by_side(*data_list)
            
        
        confirm_button = widgets.Button(description='Confirm')
        confirm_button.on_click(self.apply)
            
    def update_widget(self, name, value):
        setattr(self, name, value)
        self.refresh()
        
    def generate(self):
        pass
    
    def refresh(self):
        pass
    
    def update(self):
        pass
    
    def apply(self):
        pass