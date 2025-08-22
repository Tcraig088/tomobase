from abc import ABC, abstractmethod
import numpy as  np

class TiltScheme(ABC):
    """Base Class for a Tilt Schemes.

    This class provides the basic structure and functionality for all tilt schemes.

    Attributes:
        index (int): The current index in the tilt series.
        _isfinished (bool): Whether the tilt scheme has finished.

    """
    def __init__(self):
        self.index = 0
        self._isfinished = False

    @property
    def isfinished(self):
        return self._isfinished
    
    @abstractmethod
    def get_angle(self):
        """Get the tilt angle for the current index.

        """
        pass
    
    @abstractmethod
    def get_angle_array(self, indices):
        pass  
    
    