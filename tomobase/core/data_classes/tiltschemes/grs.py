
import numpy as np

from ...base_classes import TiltSchemeAbstract
from ...registers import tiltschemes

@tiltschemes.register(name='GRS')  
class GRS(TiltSchemeAbstract):
    """Golden Ratio Sequence tilt scheme (infinite).

    Produces a quasi-uniform sampling over [angle_min, angle_max).
    """

    def __init__(self, angle_min: float = -70, angle_max: float = 70, start_at_zero: bool = True):
        # index=1 matches your current behavior
          # if your base supports this; otherwise super().__init__(); self.index=index

        self._range_rad = np.radians(angle_max - angle_min)
        self._min_rad = np.radians(angle_min)
        self._gr = (1 + np.sqrt(5.0)) / 2.0
        
        super().__init__(angle_min, angle_max) 
        
        
        if start_at_zero:
            self.index = 0


    def _angle_at_index(self, i: int) -> float:
        # If you want to forbid i < 1 because you chose index=1:
        if i < 0:
            raise ValueError("GRS expects index >= 0 (set index=0 by default).")


    
        angle_rad = np.mod(i * self._gr * self._range_rad, self._range_rad) + self._min_rad
        return float(np.round(np.degrees(angle_rad), 2))
    
    def next_angle(self) -> float:
        return self._angle_at_index(self.index)