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
    def __init__(self, angle_min, angle_max, k=8, isbidirectional=True):
        super().__init__()
        self.angle_max = angle_max
        self.angle_min = angle_min
        self.k = k
        
        #Setting parameters
        self.isbidirectional = isbidirectional
        if isbidirectional:
            self.isforward=True
        
        self.step = (self.angle_max - self.angle_min)/(k+0.5)
        self.i = 0
        self.offset = 0
        self.offset_set = 2
        self.offset_run = 1/self.offset_set
        self.angle = 0
        self.max_cutoff = self.angle_max - (self.step/2)
        
    def get_angle(self):
        if self.isbidirectional:
            return self._get_angle_bidirectional()
        else:
            return self._get_angle_unidirectional() 
    
    def _get_angle_bidirectional(self):
        if self.i == 0:
            self.angle = self.angle_min
        elif self.isforward:
            if np.isclose(self.angle + self.step, self.angle_max) or (self.angle+self.step) > self.angle_max:
                self._get_offsets()
                self.isforward = False
                if np.isclose(self.max_cutoff + (self.step*self.offset), self.angle_max) or (self.max_cutoff + (self.step*self.offset)) >=  self.angle_max:
                    self.angle = self.max_cutoff + (self.step*self.offset) - self.step
                else:
                    self.angle = self.max_cutoff + (self.step*self.offset)
                self.step *= -1 
            else:
                self.angle = self.angle + self.step
        else:
            if np.isclose(self.angle+self.step, self.angle_max) or (self.angle+self.step) < self.angle_min:
                self._get_offsets()
                self.isforward = True
                self.angle = self.angle_min + (np.abs(self.step)*self.offset)
                self.step *= -1
            else:
                self.angle = self.angle + self.step
        self.i += 1
        return np.round(self.angle,2)
    
    
    def _get_angle_unidirectional(self):
        if self.i == 0:
            self.angle = self.angle_min
        elif np.isclose(self.angle + self.step, self.angle_max) or (self.angle + self.step) > self.angle_max:
            self._get_offsets()
            self.angle = self.angle_min + (self.step * self.offset)
        else:
            self.angle += self.step
        self.i += 1
        return np.round(self.angle, 2)
    
    def _get_offsets(self):
        if (self.offset + 0.5) >= 1:
            if self.offset == ((self.offset_set-1)/(self.offset_set)):
                self.offset_set = self.offset_set*2
                self.offset_run = 1/self.offset_set
                self.offset = self.offset_run
            else:
                self.offset_run += 2/self.offset_set
                self.offset = self.offset_run
        else:
            self.offset += 0.5  
            
    def get_angle_array(self, indices):
        return super().get_angle_array(indices)