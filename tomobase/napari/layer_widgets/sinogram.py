import napari
import numpy as np

from tomobase.napari.components import CollapsableWidget
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QComboBox, QGridLayout
from qtpy.QtCore import Qt


class SinogramDataWidget(CollapsableWidget):
    def __init__(self, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__('Details', parent)
        self.viewer = viewer
        layer = self.viewer.layers.selection.active
        
        scale = layer.scale[0]
        max_angle = str(np.round(np.max(layer.metadata['ct metadata']['angles']),2))
        min_angle = str(np.round(np.min(layer.metadata['ct metadata']['angles']),2))
        
        self.widgets_metadata = None
        
        self.label_type = QLabel('Data Type:')
        self.label_type_entry = QLabel('Sinogram')
        self.label_dtype = QLabel('Data Type:')
        self.label_dtype_entry = QLabel(str(layer.data.dtype))
        self.label_pixelsize = QLabel('Pixelsize (nm):')
        self.label_pixelsize_entry = QLabel(str(scale))
        self.label_angle_range = QLabel(f'Angle Range: %s - %s\u00B0' % (min_angle, max_angle))
        
        self.layout = QGridLayout()
        
        self.layout.addWidget(self.label_type, 0, 0)
        self.layout.addWidget(self.label_type_entry, 0, 1)
        self.layout.addWidget(self.label_dtype, 1, 0)
        self.layout.addWidget(self.label_dtype_entry, 1, 1)
        self.layout.addWidget(self.label_pixelsize, 2, 0)
        self.layout.addWidget(self.label_pixelsize_entry, 2, 1)
        self.layout.addWidget(self.label_angle_range, 3, 0, 1, 2)
        
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.show()
        
        self.viewer.dims.events.ndisplay.connect(self.updateDims)
        self.viewer.dims.events.order.connect(self.updateDims)
        self.viewer.dims.events.current_step.connect(self.updateDims)

        self.updateDims()
        
    def updateDims(self):
        layer = self.viewer.layers.selection.active
        dims = len(layer.data.shape)
        
        if self.widgets_metadata is not None:
            for i in range(len(self.widgets_metadata)):
                self.layout.removeWidget(self.widgets_metadata[i])
                self.widgets_metadata[i].hide()
            self.widgets_metadata = None
            
        if dims > self.viewer.dims.ndisplay:
            label_dict =  {}
            for i in range(dims - self.viewer.dims.ndisplay):
                dim_index = self.viewer.dims.order[i]
                label = layer.metadata['ct metadata']['axis'][dim_index]
                index = self.viewer.dims.current_step[dim_index]
                if label == 'Projections':
                    angle = layer.metadata['ct metadata']['angles'][index]
                    label_dict['Angle (\u00B0):'] = str(np.round(angle,2))
                    label_dict['Projection:'] = str(index)
                elif label == 'Signals':
                    if 'signals' in layer.metadata['ct metadata']:
                        label_dict['Current Signal:'] = layer.metadata['ct metadata']['signals'][index]
                    else:
                        label_dict['Signal:'] = str(index)
                else:
                    label_dict[label] = str(np.round(index*layer.scale[0]))
               
            self.widgets_metadata = [] 
            i = 0   
            for key, value in label_dict.items():
                widget_label = QLabel(key)
                widget_value = QLabel(value)
                self.layout.addWidget(widget_label, 4+i, 0)
                self.layout.addWidget(widget_value, 4+i, 1)
                
                self.widgets_metadata.append(widget_label)
                self.widgets_metadata.append(widget_value)
                i+=1
                
            self.layout.setAlignment(Qt.AlignTop)
            self.show()
