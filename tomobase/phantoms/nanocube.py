import numpy as np

from qtpy.QtWidgets import QHBoxLayout, QVBoxLayout, QComboBox, QLabel, QWidget, QFrame, QGridLayout, QPushButton, QSpinBox, QDialog
from PyQt5.QtCore import Qt

def load_cube(size=256,dim=512):
    obj = np.zeros((dim,dim,dim),dtype=np.float32)
    start = int(dim//2-size//2)
    end = int(dim//2+size//2)
    obj[start:end,start:end,start:end] = 1
    return obj

class CubeWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Create the layout
        self.layout = QHBoxLayout()
        
        # Create the buttons and spin boxes
        self.sizeSpinBox = QSpinBox()
        self.dimSpinBox = QSpinBox()

        # Add the widgets to the layout
        self.layout.addWidget(QLabel("Size:"))
        self.layout.addWidget(self.sizeSpinBox)
        self.layout.addWidget(QLabel("Dimension:"))
        self.layout.addWidget(self.dimSpinBox)

        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)
        self.show()
        
    def get_volume(self):
        size = self.sizeSpinBox.value()
        dim = self.dimSpinBox.value()
        return load_cube(size,dim)
