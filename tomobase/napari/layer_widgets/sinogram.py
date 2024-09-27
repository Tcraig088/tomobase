import napari
import numpy as np

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel
from qtpy.QtCore import Qt


class SinogramDataWidget(QWidget):
    def __init__(self, layer, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__(parent)
        self.layer= layer
        self.viewer = viewer
        
        scale = layer.metadata['ct metadata']['pixel_size'][0]
        max_angle = str(np.round(np.max(layer['ct metadata']['angles']),2))
        min_angle = str(np.round(np.min(layer['ct metadata']['angles']),2))
        
        self.label_name = QLabel(layer['name'])
        self.label_type = QLabel = QLabel('Data Type: Sinogram')
        self.label_pixelsize = QLabel(f'Pixel Size: %s nm' % np.round(scale,2))
        self.label_angle_range = QLabel(f'Angle Range: %s - %s\u00B0' % (min_angle, max_angle))
        
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.show()