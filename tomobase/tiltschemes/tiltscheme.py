from abc import ABC, abstractmethod
import numpy as  np

class TiltScheme(ABC):
    """Base Class for a Tilt Scheme Plugin.

    Attributes:
        index (int): The index of the data type in the library
        isfinished (bool): Whether the tilt scheme is finished. Set to true on the last angle in the series if the scheme has a termination point.
                
    Methods:
        get_angle(): Returns the next tilt angle in the scheme must be set for the child classes.
    """
    def __init__(self):
        self.index = 0
        self._isfinished = False

    @property
    def isfinished(self):
        return self._isfinished
    
    @abstractmethod
    def get_angle(self, index=None):
        pass
    
    @abstractmethod
    def get_angle_array(self, indices):
        pass  
    
    