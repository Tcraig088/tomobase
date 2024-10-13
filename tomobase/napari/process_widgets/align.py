import numpy as np
import napari
import inspect
from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

from tomobase.log import logger
from tomobase.data import Volume, Sinogram
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.registrations.tiltschemes import TOMOBASE_TILTSCHEMES
from tomobase.processes import project

class AlignWidget(QWidget):
    def __init__(self, process_name, process,  viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__(parent)
 
        self.viewer = viewer
        self.label_data = QLabel('Sinogram:')
        self.combobox_select = QComboBox()
        self.onLayerNumberChange()
        self.onLayerSelectChange()
        
        self.process_name = process_name
        self.process = process
        if process.widget is not None:
            self.process_widget = process.widget()
        else:
            self.process_widget = None
        self.button_confirm = QPushButton('Confirm')
        
        self.layout = QGridLayout()
        self.layout.addWidget(self.label_data, 0, 0)
        self.layout.addWidget(self.combobox_select, 0, 1)
        if process.widget is not None:
            self.layout.addWidget(self.process_widget, 1, 0, 1, 3)
        self.layout.addWidget(self.button_confirm, 2, 0)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        
        self.viewer.layers.events.inserted.connect(self.onLayerNumberChange)
        self.viewer.layers.events.removed.connect(self.onLayerNumberChange)
        self.viewer.layers.selection.events.changed.connect(self.onLayerSelectChange)
        self.combobox_select.currentIndexChanged.connect(self.onSinogramChange)
        self.button_confirm.clicked.connect(self.onConfirm)
        
        
    def onLayerNumberChange(self):  
        self.combobox_select.clear()
        self.combobox_select.addItem('Select Sonogram')
        for layer in self.viewer.layers:
            if layer is not None:
                if 'ct metadata' in layer.metadata:
                    if layer.metadata['ct metadata']['type'] == TOMOBASE_DATATYPES.SINOGRAM.value():
                        self.combobox_select.addItem(layer.name)
        self.combobox_select.setCurrentIndex(0)
        active_layer = self.viewer.layers.selection.active
        if active_layer is not None:
            self.onLayerSelectChange()
            
    def onSinogramChange(self, index):
        if self.combobox_select.currentIndex() > 0:
            text = self.combobox_select.currentText()
            for layer in self.viewer.layers:
                if layer.name == text:
                    self.viewer.layers.selection.active = layer
        else:
            if self.viewer.layers.selection.active is not None:
                self.viewer.layers.selection.active = None

    def onLayerSelectChange(self):
        active_layer = self.viewer.layers.selection.active
        if active_layer is None:
            self.combobox_select.setCurrentIndex(0)
            return 
        
        if 'ct metadata' in active_layer.metadata:
            if active_layer.metadata['ct metadata']['type'] == TOMOBASE_DATATYPES.SINOGRAM.value():
                if active_layer.name != self.combobox_select.currentText():
                    self.combobox_select.setCurrentText(active_layer.name)
            else:
                self.combobox_select.setCurrentIndex(0)
        else:
            self.combobox_select.setCurrentIndex(0)
            
    def onConfirm(self):
        isvalid = True
        if self.combobox_select.currentIndex() == 0:
            logger.warning('No sinogram selected')
            isvalid = False
            
        if isvalid:
            name = self.viewer.layers.selection.active.name
            sino = Sinogram._from_napari_layer(self.viewer.layers.selection.active)
            if self.process_widget is not None:
                sino = self.process_widget.process(sino)
            elif inspect.isclass(self.process):
                sino = self.process().run(sino)
            else:
                sino = self.process(sino)
            
            _dict ={}
            _dict['viewsettings'] = {}
            _dict['viewsettings']['colormap'] = 'gray'  
            _dict['viewsettings']['contrast_limits'] = [0,255]
            _dict['name'] = name +' ' + self.process_name
            self.viewer.dims.ndisplay = 2
            layer = sino._to_napari_layer(astuple=False, **_dict)
            self.viewer.add_layer(layer)
            