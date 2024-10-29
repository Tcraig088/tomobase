import numpy as np
import napari
import inspect
from collections.abc import Iterable
import time

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QCheckBox, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

from tomobase.log import logger
from tomobase.data import Volume, Sinogram
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.registrations.tiltschemes import TOMOBASE_TILTSCHEMES
from tomobase.napari.components import CollapsableWidget
from tomobase.napari.layer_widgets.layerselect import LayerSelctWidget
from tomobase.napari.utils import get_value, get_widget, connect

from threading import Thread

class ProcessWidget(QWidget):
    def __init__(self, process:dict, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__(parent)
        
        # Define States
        self.isinitialized = False
        self.isrunning = False
        
        # Define Viewer
        self.viewer = viewer
        
        #Define Common Widgets
        self.button_confirm = QPushButton('Confirm')
        self.button_initialize = QPushButton('Initialize')
        self.button_initialize.setVisible(False)
        
        # Define Process Handling Variables
        self.process = process['controller'].controller
        self.name = process['name']
        self.custom_widgets = {
            'Name': [],
            'Label': [],
            'Widget': []
        }

        
        if inspect.isclass(self.process):
            self.setupFromClass()
        else:
            self.setupFromFunc()
        
        self.layout = QGridLayout()
        self.layout.addWidget(self.layer_select, 0, 0 , 1, 2)
        self.layout.addWidget(self.button_initialize, 1, 0)
               
        i=2
        for j, key in enumerate(self.custom_widgets['Name']):
            self.layout.addWidget(self.custom_widgets['Label'][j], j+i, 0)
            self.layout.addWidget(self.custom_widgets['Widget'][j], j+i, 1)
        i +=i
        
        
        self.layout.addWidget(self.button_confirm, i+2, 0)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        
        self.button_confirm.clicked.connect(self.onConfirm)
        self.button_initialize.clicked.connect(self.initializeClass)
        
    def setupFromFunc(self):
        signature = inspect.signature(self.process)
        banned = ['self','sino', 'vol', 'kwargs']
        
        first_param = next(param for name, param in signature.parameters.items() if name != 'self')
        logger.debug(f'First param: {first_param}')
        self.layer_select = LayerSelctWidget([first_param.annotation.get_type_id()], True, self.viewer)

        for name, param in signature.parameters.items():
            if name not in banned:
                wname, wlabel, widget = get_widget(name, param)
                if wname is not None:
                    self.custom_widgets['Widget'].append(widget)
                    self.custom_widgets['Name'].append(wname)
                    self.custom_widgets['Label'].append(wlabel)
    
    def setupFromClass(self):
        signature = inspect.signature(self.process.__init__)
        first_param = next(param for name, param in signature.parameters.items() if name != 'self')
        self.layer_select = LayerSelctWidget([first_param.annotation.get_type_id()], True, self.viewer)
        
        self.button_initialize.setVisible(True)
        banned = ['self', 'sino', 'vol','kwargs']
        for name, param in signature.parameters.items():
            if name not in banned:
                wname, wlabel, widget = get_widget(name, param)
                if wname is not None:
                    self.custom_widgets['Widget'].append(widget)
                    self.custom_widgets['Name'].append(wname)
                    self.custom_widgets['Label'].append(wlabel)
        
    def initializeClass(self):
        if self.isinitialized:
            return
        
        self.isinitialized = True
        layer = self.layer_select.getLayer()
        sino = Sinogram._from_napari_layer(layer)  
        dict_args = {'sino':sino}
        for i, key in enumerate(self.custom_widgets['Name']):
            dict_args[self.custom_widgets['Name'][i]] = get_value(self.custom_widgets['Widget'][i])
            
        self.process = self.process(**dict_args)
        presets = self.process.generate()
        
        for widget in self.custom_widgets['Widget']:
            connect(widget, self.updateTempLayer)
        
        self.layers = []
        if isinstance(presets, Iterable):
            for i in presets:
                if isinstance(i, Sinogram):
                    _dict = {}
                    _dict['viewsettings'] = {}
                    _dict['viewsettings']['colormap'] = 'gray'  
                    _dict['viewsettings']['contrast_limits'] = [0,np.max(i.data)]
                    self.viewer.dims.ndisplay = 2
                    layer = i._to_napari_layer(astuple=False, **_dict)
                    self.viewer.add_layer(layer)
                    self.layers.append(layer)
        else:
            if isinstance(presets, Sinogram):
                _dict = {}
                _dict['viewsettings'] = {}
                _dict['viewsettings']['colormap'] = 'gray'  
                _dict['viewsettings']['contrast_limits'] = [0,np.max(presets.data)]
                self.viewer.dims.ndisplay = 2
                layer = presets._to_napari_layer(astuple=False, **_dict)
                self.viewer.add_layer(layer)
                self.layers.append(layer)
                
    def onConfirm(self):
        pass
    
        
    def updateTempLayer(self):
        logger.debug('Updating temp layer')
        if self.isinitialized and (not self.isrunning):
            threaded_func = Thread(target=self.waitForUpdates)
            threaded_func.start()
    
    def waitForUpdates(self):
        self.isrunning = True
        time.sleep(1)
        for i, key in enumerate(self.custom_widgets['Name']):
            setattr(self.process, self.custom_widgets['Name'][i], get_value(self.custom_widgets['Widget'][i]))  
            
        logger.debug(self.process.threshold)
        outputs = self.process.update()
        if not isinstance(outputs, Iterable):
            outputs = [outputs]
        for i, layer in enumerate(self.layers):
            layer.data = outputs[i].data
            layer.refresh()
        self.isrunning = False