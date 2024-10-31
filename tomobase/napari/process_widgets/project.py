import numpy as np
import napari

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

from tomobase.log import logger
from tomobase.data import Volume, Sinogram
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.registrations.tiltschemes import TOMOBASE_TILTSCHEMES


class ProjectWidget(QWidget):
    def __init__(self, name, process, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__(parent)

        self.process = process.controller
        self.viewer = viewer
        self.label_data = QLabel('Volume:')
        self.combobox_select = QComboBox()
        self.onLayerNumberChange()
        self.onLayerSelectChange()
        
        self.label_angles = QLabel('Number of Angles:')
        self.spin_angles = QSpinBox()
        self.spin_angles.setRange(1, 100000)
        self.spin_angles.setValue(1)
        
        self.label_tiltscheme = QLabel('Tilt Scheme:')  
        self.combobox_tiltscheme = QComboBox()
        self.combobox_tiltscheme.addItem('Select Tilt Scheme')
        for key, value in TOMOBASE_TILTSCHEMES.items():
            self.combobox_tiltscheme.addItem(key.lower())
        self.combobox_tiltscheme.setCurrentIndex(0)
        self.widget_tiltscheme = None
        
        self.button_confirm = QPushButton('Confirm')
        
        self.layout = QGridLayout()
        self.layout.addWidget(self.label_data, 0, 0)
        self.layout.addWidget(self.combobox_select, 0, 1)
        self.layout.addWidget(self.label_angles, 1, 0)
        self.layout.addWidget(self.spin_angles, 1, 1)
        self.layout.addWidget(self.label_tiltscheme, 2, 0)
        self.layout.addWidget(self.combobox_tiltscheme, 2, 1)
        self.layout.addWidget(self.button_confirm, 4, 0)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        
        self.viewer.layers.events.inserted.connect(self.onLayerNumberChange)
        self.viewer.layers.events.removed.connect(self.onLayerNumberChange)
        self.combobox_tiltscheme.currentIndexChanged.connect(self.onTiltschemeChange)
        self.viewer.layers.selection.events.changed.connect(self.onLayerSelectChange)
        self.combobox_select.currentIndexChanged.connect(self.onVolumeChange)
        self.button_confirm.clicked.connect(self.onConfirm)
        
        
    def onLayerNumberChange(self):  
        self.combobox_select.clear()
        self.combobox_select.addItem('Select Volume')
        for layer in self.viewer.layers:
            if layer is not None:
                if 'ct metadata' in layer.metadata:
                    if layer.metadata['ct metadata']['type'] == TOMOBASE_DATATYPES.VOLUME.value():
                        self.combobox_select.addItem(layer.name)
        self.combobox_select.setCurrentIndex(0)
        active_layer = self.viewer.layers.selection.active
        if active_layer is not None:
            self.onLayerSelectChange()
            
    def onTiltschemeChange(self, index):
        if self.widget_tiltscheme is not None:
            self.layout.removeWidget(self.widget_tiltscheme)
            self.widget_tiltscheme.deleteLater()
            self.widget_tiltscheme = None
            
        if self.combobox_tiltscheme.currentIndex() > 0:
            tiltscheme = TOMOBASE_TILTSCHEMES[self.combobox_tiltscheme.currentText().upper()]
            self.widget_tiltscheme = tiltscheme.widget()
            logger.debug(f"Widget: {self.widget_tiltscheme}")
            self.layout.addWidget(self.widget_tiltscheme, 3, 0, 1, 3)
            self.widget_tiltscheme.show()
        
         
    def onVolumeChange(self, index):
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
            if active_layer.metadata['ct metadata']['type'] == TOMOBASE_DATATYPES.VOLUME.value():
                if active_layer.name != self.combobox_select.currentText():
                    self.combobox_select.setCurrentText(active_layer.name)
            else:
                self.combobox_select.setCurrentIndex(0)
        else:
            self.combobox_select.setCurrentIndex(0)
            
    def onConfirm(self):
        isvalid = True
        if self.combobox_select.currentIndex() == 0:
            logger.warning('No volume selected')
            isvalid = False
        if self.combobox_tiltscheme.currentIndex() == 0:
            logger.warning('No tilt scheme selected')
            isvalid = False
        if self.spin_angles.value() < 1:
            logger.warning('Invalid number of angles')
            isvalid = False
            
        if isvalid:
            name = self.viewer.layers.selection.active.name
            volume = Volume._from_napari_layer(self.viewer.layers.selection.active)
            scheme = self.widget_tiltscheme.setTiltScheme() 
            angles = np.array([scheme.get_angle() for i in range(scheme.index, self.spin_angles.value())])
            sino = self.process(volume, angles)
            
            _dict ={}
            _dict['viewsettings'] = {}
            _dict['viewsettings']['colormap'] = 'gray'  
            _dict['viewsettings']['contrast_limits'] = [0,3]
            _dict['name'] = name +' Sinogram'
            self.viewer.dims.ndisplay = 2
            layer = sino._to_napari_layer(astuple=False, **_dict)
            self.viewer.add_layer(layer)
