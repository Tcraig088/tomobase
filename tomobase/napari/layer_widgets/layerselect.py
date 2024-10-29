
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.napari.components.collapsable import CollapsableWidget
from qtpy.QtWidgets import QWidget, QLabel, QComboBox, QGridLayout
from qtpy.QtCore import Qt
class LayerSelctWidget(CollapsableWidget):
    def __init__(self, layer_types, isfixed, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__('', parent)
        
        self.viewer = viewer
        self.layer_types = layer_types
        self.isfixed = isfixed
        
        self.label_data = QLabel('Selected:')
        self.combobox_select = QComboBox()
        self.onLayerNumberChange()
        
        if self.isfixed:
            self.onLayerSelectChange()
        
        self.combobox_types = QComboBox()
        self.combobox_types.addItem('Selectable Datatypes')
        for layer_type in layer_types:
            self.combobox_types.addItem(TOMOBASE_DATATYPES.key(layer_type).capitalize())
        self.combobox_types.setCurrentIndex(0)
        
        self.layout = QGridLayout()
        self.layout.addWidget(self.label_data, 0, 0)
        self.layout.addWidget(self.combobox_select, 0, 1)
        self.layout.addWidget(self.combobox_types, 0, 2)
        
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        
        self.viewer.layers.events.inserted.connect(self.onLayerNumberChange)
        self.viewer.layers.events.removed.connect(self.onLayerNumberChange)
        self.combobox_select.currentIndexChanged.connect(self.onLayerComboboxChange)
        
        if self.isfixed:
            self.viewer.layers.selection.events.changed.connect(self.onLayerSelectChange)
        
        
    def onLayerNumberChange(self):  
        self.combobox_select.clear()
        self.combobox_select.addItem('Select Layer')
        for layer in self.viewer.layers:
            if layer is not None:
                if 'ct metadata' in layer.metadata:
                    if layer.metadata['ct metadata']['type'] in self.layer_types:
                        self.combobox_select.addItem(layer.name)
        self.combobox_select.setCurrentIndex(0)
        active_layer = self.viewer.layers.selection.active
        if active_layer is not None:
            self.onLayerSelectChange()
            
    def onLayerComboboxChange(self, index):
        if self.combobox_select.currentIndex() > 0:
            text = self.combobox_select.currentText()
            if self.isfixed:
                for layer in self.viewer.layers:
                    if layer.name == text:
                        self.viewer.layers.selection.active = layer
        else:
            if self.isfixed:
                if self.viewer.layers.selection.active is not None:
                    self.viewer.layers.selection.active = None

    def onLayerSelectChange(self):
        active_layer = self.viewer.layers.selection.active
        if active_layer is None:
            self.combobox_select.setCurrentIndex(0)
            return 
        
        if 'ct metadata' in active_layer.metadata:
            if active_layer.metadata['ct metadata']['type'] in self.layer_types:
                if active_layer.name != self.combobox_select.currentText():
                    self.combobox_select.setCurrentText(active_layer.name)
            else:
                self.combobox_select.setCurrentIndex(0)
        else:
            self.combobox_select.setCurrentIndex(0)
            
    def getLayer(self):
        for layer in self.viewer.layers:
            if layer.name == self.combobox_select.currentText():
                return layer