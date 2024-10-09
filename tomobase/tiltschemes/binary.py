
import numpy as np

from qtpy.QtWidgets import QDoubleSpinBox, QSpinBox, QGridLayout, QLabel

from tomobase.napari.components import CollapsableWidget
from tomobase.tiltschemes.tiltscheme import Tiltscheme
from tomobase.hooks import tomobase_hook_tiltscheme

from tomobase.log import logger


@tomobase_hook_tiltscheme('BINARY')
class BinaryWidget(CollapsableWidget):
    def __init__(self, parent=None):
        super().__init__('Binary Decomposition TiltScheme', parent)
        
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
        return Binary(self.angle_max.value(), self.angle_min.value(), self.index.value())
    
@tomobase_hook_tiltscheme('BINARY')  
class Binary(Tiltscheme):
    def __init__(self, angle_max, angle_min, k=8):
        super().__init__()
        self.angle_max = angle_max
        self.angle_min = angle_min
        self.step = (self.angle_max - self.angle_min)/k
        self.angle = self.angle_min
        self.conventional = False
        self.forward_offset = 0
        
        self.offset = 0
        self.runs = 1
        self.target = 1
        self.prescan = True
        
    def get_angle(self):
        target_angle = self.angle_max - self.step
        angle = self.angle + self.step
        logger.debug(f'Angle: {angle} is conventional: {self.conventional}')
        if self.index == 0:
            self.angle = self.angle_min 
        elif angle >= self.angle_max:
            if self.conventional:
                self.angle = self.angle_min + (self.get_offset()*self.step)
            else:
                self.forward_offset = self.get_offset()
                self.angle = self.angle + (self.forward_offset*np.abs(self.step))
                self.step = -1*self.step
        elif (self.step < 0) and (angle <= self.angle_min + (self.forward_offset*np.abs(self.step))):
            self.forward_offset = self.get_offset()
            self.step = -1*self.step
            self.angle = self.angle_min + (self.forward_offset*np.abs(self.step))
        else:
            self.angle = self.angle + self.step    
        self.index += 1
        
        return np.round(self.angle,2)
    
    def get_angle_array(self, indices, conventional=False):
        self.conventional =  conventional
        val = np.array([self.get_angle() for i in indices])
        self.conventional = True
        self.index = 0
        return val


    def get_offset(self):
        offset_int = 0.5**(self.target-1)
        offset_prior = 0.5**(self.target-2)
        logger.debug(f'target: {self.target}')
        
        if self.runs == self.target:
            self.target = self.target*2
            self.runs = 1
            logger.debug(f'reset')
        else:
            self.runs += 1
        
        if self.runs == 1:
            self.offset = offset_int
            logger.debug(f'Offset first: {self.offset}')
            offset = self.offset
        elif self.runs % 2 == 0:
            offset = self.offset + offset_prior
            logger.debug(f'Offset remainder: {offset}')
            offset = offset
        else:
            self.offset = self.offset + (2*offset_int)
            logger.debug(f'Offset increment: {self.offset}')
            offset = self.offset
            
        return offset
            