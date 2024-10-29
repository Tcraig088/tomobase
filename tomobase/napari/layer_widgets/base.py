
import napari

from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel
from qtpy.QtCore import Qt

class QWidget:
    def __init__(self, viewer:napari.viewer.Viewer, parent=None):
        super().__init__(parent)
        self.viewer = viewer
        
        self.label_name = QLabel('Name:')
        self.label_name_entry = QLabel('None Selected')
        
        self.label_type = QLabel('Data Type:')
        self.label_type_entry = QLabel('NA')
        
        self.label_pixelsize = QLabel('Pixel Size (nm):')
        self.label_pixelsize_entry = QLabel('NA')
        
        self.widget = None 
        
        self.layout = QVBoxLayout()
        pass