
import numpy as np

from qtpy.QtWidgets import QDoubleSpinBox, QSpinBox, QGridLayout, QLabel

from tomobase.napari.components import CollapsableWidget
from tomobase.tiltschemes.tiltscheme import Tiltscheme
from tomobase.hooks import tomobase_hook_tiltscheme


@tomobase_hook_tiltscheme('GRS')
class GRSWidget(CollapsableWidget):
    def __init__(self, parent=None):
        super().__init__('GRS TiltScheme', parent)
        
        self.angle_max = QDoubleSpinBox()
        self.angle_max.setRange(-90, 90)
        self.angle_max.setValue(70)
        
        self.angle_min = QDoubleSpinBox()
        self.angle_min.setRange(-90, 90)
        self.angle_min.setValue(-70)
        
        self.index = QSpinBox()
        self.index.setRange(1, 1000)
        self.index.setValue(1)
        
        self.layout = QGridLayout()
        self.layout.addWidget(QLabel("Angle Max ('\u00B0')"), 0, 0)
        self.layout.addWidget(self.angle_max, 0, 1)
        self.layout.addWidget(QLabel("Angle Min ('\u00B0')"), 1, 0)
        self.layout.addWidget(self.angle_min, 1, 1)
        self.layout.addWidget(QLabel("Index"), 2, 0)
        self.layout.addWidget(self.index, 2, 1)
        
        self.setLayout(self.layout)
        
    def setTiltScheme(self):
        return GRS(self.angle_max.value(), self.angle_min.value(), self.index.value())
    
@tomobase_hook_tiltscheme('GRS')  
class GRS(Tiltscheme):
    def __init__(self, angle_min, angle_max, index=1):
        super().__init__()
        self.angle_max = angle_max
        self.angle_min = angle_min
        self.range = np.radians(angle_max - angle_min)
        self.gr = (1+np.sqrt(5))/2
        self.index = index

        
    def get_angle(self):
        angle_rad = np.mod(self.index*self.gr*self.range, self.range) + np.radians(self.angle_min)
        self.index += 1
        return np.round(np.degrees(angle_rad),2)
    
    def get_angle_array(self, indices):
        angles = np.mod(indices*self.gr*self.range, self.range) + np.radians(self.angle_min)
        return np.round(np.degrees(angles),2)