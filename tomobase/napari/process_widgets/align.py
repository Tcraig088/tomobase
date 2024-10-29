import numpy as np
import napari
import inspect
from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QCheckBox, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

from tomobase.log import logger
from tomobase.data import Volume, Sinogram
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.registrations.tiltschemes import TOMOBASE_TILTSCHEMES
from tomobase.napari.components import CollapsableWidget
from tomobase.napari.utils import get_value, get_widget
from tomobase.napari.process_widgets.process import ProcessWidget

from threading import Thread

class AlignWidget(ProcessWidget):
    def __init__(self, process:dict, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__(process=process, viewer=viewer, parent=None)
        self.name = process['name']

    def _onConfirmFunction(self):
        layer = self.layer_select.getLayer()
        if layer is None:
            logger.error('No layer selected or the selected layer is not a sinogram')
            return
        
        sino = Sinogram.from_data_tuple(layer)
        values = {}
        for i, key in enumerate(self.custom_widgets['Name']):
            values[key] = get_value(self.custom_widgets['Widget'][i])
        
        threaded_process = Thread(target=self.process, args=(sino,), kwargs=values)
        outs = threaded_process.start()
        if 'extend_returns' in values:
            if values['extend_returns'] == True:
                sino = outs.pop(0)
            else:
                sino = outs
        else:
            sino = outs
        
        logger.info(f'Process {self.name} completed')  
        if 'inplace' in values:
            if values['inplace'] == True:
                layer.refresh()
                return
        
        layer = sino.to_data_tuple(attributes={'name': layer.name + ' ' + self.name})
        self.viewer.dims.ndisplay = 2
        self.viewer.add_layer(layer)
        
        
        
    def _onConfirmClass(self):
        layer = self.layer_select.getLayer()
        if layer is None:
            logger.error('No layer selected or the selected layer is not a sinogram')
            return
        
        sino = Sinogram.from_data_tuple(layer)
        values = {}
        for i, key in enumerate(self.custom_widgets['Name']):
            values[key] = get_value(self.custom_widgets['Widget'][i])
            setattr(self.process, key, self.custom_widgets['Widget'][i])
        
        threaded_process = Thread(target=self.process.apply)
        outs = threaded_process.start()
        if 'extend_returns' in values:
            if values['extend_returns'] == True:
                sino = outs.pop(0)
            else:
                sino = outs
        else:
            sino = outs
        
        logger.info(f'Process {self.name} completed')  
        
        if 'inplace' in values:
            if values['inplace'] == True:
                layer.refresh()
                return
        
        layer = sino.to_data_tuple(attributes={'name': layer.name + ' ' + self.name})
        self.viewer.dims.ndisplay = 2
        self.viewer.add_layer(layer)
        
        self.layers.               
    def onConfirm(self):
        isvalid = True
        layer = self.layer_select.getLayer()
        
        if isvalid:
            name = layer.name
            sino = Sinogram._from_napari_layer(layer)
            
            dict_args = {}
            for i, key in enumerate(self.custom_widgets['Name']):
                dict_args[self.custom_widgets['Name'][i]] = get_value(self.custom_widgets['Widget'][i])
                
            if not inspect.isclass(self.process): 
                logger.debug(f'Running {self.name} with {dict_args}')
                outs = self.process(sino, **dict_args)
                if 'extend_returns' in dict_args:
                    sino = outs.pop(0)
                else:
                    sino = outs
                    
                if 'inplace' in dict_args:
                    if dict_args['inplace'] == True:
                        layer.refresh()
                        return

                logger.info(f'Process {self.name} completed')
                _dict ={}
                _dict['viewsettings'] = {}
                _dict['viewsettings']['colormap'] = 'gray'  
                _dict['viewsettings']['contrast_limits'] = [0,np.max(sino.data)]
                _dict['name'] = name +' ' + self.name
                self.viewer.dims.ndisplay = 2
                layer = sino._to_napari_layer(astuple=False, **_dict)
                self.viewer.add_layer(layer)

    
        
        