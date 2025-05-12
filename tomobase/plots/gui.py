import pyqtgraph as pg
import qtpy 
from qtpy.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout,  QLabel, QCheckBox, QComboBox, QGridLayout, QSpinBox, QDoubleSpinBox, QLineEdit

class BaseGui(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tomoography GUI")
        
        
        