
import numpy as np

from .tiltscheme import TiltScheme
from ..hooks import tiltscheme_hook

@tiltscheme_hook('GRS')  
class GRS(TiltScheme):
    """Golden Ratio Sequence Tilt Scheme.

    Attributes:
        angle_min (float): The minimum angle in the tilt series.
        angle_max (float): The maximum angle in the tilt series.
        index (int): The index to start acquisition from.
    """

    def __init__(self, angle_min:float=-70, angle_max:float=70, index:int=1):
        """Initialize the Golden Ratio Sequence Tilt Scheme.

        Args:
            angle_min (float, optional): The minimum angle in the tilt series. Defaults to -70.
            angle_max (float, optional): The maximum angle in the tilt series. Defaults to 70.
            index (int, optional): The index to start acquisition from. Defaults to 1.
        """
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
    
