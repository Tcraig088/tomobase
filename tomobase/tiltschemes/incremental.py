
import numpy as np

from qtpy.QtWidgets import QDoubleSpinBox, QSpinBox, QGridLayout, QLabel

from tomobase.napari.components import CollapsableWidget
from tomobase.tiltschemes.tiltscheme import Tiltscheme
from tomobase.hooks import tomobase_hook_tiltscheme


@tomobase_hook_tiltscheme('INCREMENTAL')
class IncrementalWidget(CollapsableWidget):
    def __init__(self, parent=None):
        super().__init__('Incremental TiltScheme', parent)
        
        self.angle_start = QDoubleSpinBox()
        self.angle_start.setRange(-90, 90)
        self.angle_start.setValue(-70)
        
        self.angle_end = QDoubleSpinBox()
        self.angle_end.setRange(-90, 90)
        self.angle_end.setValue(70)
        
        self.step = QDoubleSpinBox()
        self.step.setRange(0, 90)
        self.step.setValue(2)

        self.layout = QGridLayout()
        self.layout.addWidget(QLabel("Angle Start ('\u00B0')"), 0, 0)
        self.layout.addWidget(self.angle_start, 0, 1)
        self.layout.addWidget(QLabel("Angle End ('\u00B0')"), 1, 0)
        self.layout.addWidget(self.angle_end, 1, 1)
        self.layout.addWidget(QLabel("Step ('\u00B0')"), 2, 0)
        self.layout.addWidget(self.step, 2, 1)

        self.setLayout(self.layout)
        
    def setTiltScheme(self):
        return Incremental(self.angle_start.value(), self.angle_end.value(), self.step.value())
    
@tomobase_hook_tiltscheme('INCREMENTAL')  
class Incremental(Tiltscheme):
    def __init__(self, angle_start, angle_end, step):
        super().__init__()
        self.angle_start = angle_start
        self.angle_end = angle_end  
        self.step = step

        
    def get_angle(self):
        angle = self.angle_start + (self.index*self.step)
        self.index += 1
        if self.angle_end > self.angle_start:
            if angle + self.step > self.angle_end:
                self._isfinished = True
        else:
            if angle + self.step < self.angle_end:
                self._isfinished = True
        return angle
    
    def get_angle_array(self, indices):
        return self.angle_start + (indices*self.step)