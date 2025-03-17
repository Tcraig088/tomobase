import numpy as np

from tomobase.hooks import tomobase_hook_tiltscheme
from tomobase.tiltschemes.tiltscheme import TiltScheme

@tomobase_hook_tiltscheme('INCREMENTAL')  
class Incremental(TiltScheme):
    def __init__(self, angle_start:float=-70, angle_end:float=70, step:float=2):
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