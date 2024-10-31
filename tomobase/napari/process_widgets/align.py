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
        
        layerdata = sino.to_data_tuple(attributes={'name': layer.name + ' ' + self.name})
        self.viewer.dims.ndisplay = 2
        self.viewer._add_layer_from_data(*layerdata)
         
    def _onConfirmClass(self):
        layer = self.layer_select.getLayer()
        if layer is None:
            logger.error('No layer selected or the selected layer is not a sinogram')
            return
        
        sino = Sinogram.from_data_tuple(self.selected_layer)
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
                self.selected_layer.refresh()
                return
        
        layerdata = sino.to_data_tuple(attributes={'name': layer.name + ' ' + self.name})
        self.viewer.dims.ndisplay = 2
        self.viewer._add_layer_from_data(*layerdata)
             
    def onConfirm(self):
        if inspect.isfunction(self.process):
            self._onConfirmFunction()
        else:
            self._onConfirmClass()

    
        
        