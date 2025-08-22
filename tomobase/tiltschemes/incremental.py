import numpy as np

from ..hooks import tiltscheme_hook
from .tiltscheme import TiltScheme

@tiltscheme_hook('INCREMENTAL')  
class Incremental(TiltScheme):
    """Incremental Tilt Scheme.

    Attributes:
        angle_start (float): The starting angle for the tilt series.
        angle_end (float): The ending angle for the tilt series.
        step (float): The step size for each increment.
    """
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
    
