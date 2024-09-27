import napari
import numpy as np

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel
from qtpy.QtCore import Qt


class ImageDataWidget(QWidget):
    def __init__(self, layer, viewer: 'napari.viewer.Viewer', parent=None):
        super().__init__(parent)
        self.layer= layer
        self.viewer = viewer
        
        scale = layer.metadata['ct metadata']['pixel_size'][0]

        self.label_name = QLabel(layer['name'])
        self.label_type = QLabel = QLabel('Data Type: Image')
        self.label_pixelsize = QLabel(f'Pixel Size: %s nm' % np.round(scale,2))
  
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.show()