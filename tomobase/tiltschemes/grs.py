
import numpy as np

from qtpy.QtWidgets import QDoubleSpinBox, QSpinBox, QGridLayout, QLabel

from tomobase.tiltschemes.tiltscheme import Tiltscheme
from tomobase.hooks import tomobase_hook_tiltscheme
 
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