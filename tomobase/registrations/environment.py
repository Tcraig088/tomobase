import enum
import logging
from tomobase.log import logger

class GPUContext(enum.Enum):
    CUPY = 1
    NUMPY = 2

class EnvironmentContext():
    """
    Singleton class to check if submodules are available or not.

    Attributes:
    tomobase (bool): True if tomobase is available, False otherwise.
    tomoacquire (bool): True if tomoacquire is available, False otherwise.
    
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnvironmentContext, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._cupy_checked = False
        self._cupy_available = False
        
        self.context = GPUContext.NUMPY
        self.device = 0
        
    def set_context(self, context:GPUContext=GPUContext.NUMPY, device:int=0):
        if context == GPUContext.CUPY:
            if not self._cupy_checked:
                self._cupy_checked = True
                try:
                    import cupy as cp
                    self._cupy_available = True
                except ModuleNotFoundError:
                    self._cupy_available = False
                    logging.warning("CUPY module not found. Please Install from Conda or pip. Context unchanged.")
                except Exception as e:
                    self._cupy_available = False
                    logging.error(e)
                    
            if self._cupy_available:
                #check their is a GPU available with the device id
                if cp.cuda.runtime.getDeviceCount() <= device:
                    logging.warning("No GPU available with device id {}".format(device))
                else:
                    self.context = GPUContext.CUPY
                    self.device = device
                    
        elif context == GPUContext.NUMPY:
            self.context = GPUContext.NUMPY
            self.device = device
            
        else:
            logging.warning("Unknown context. Context unchanged.")
            return
    
xp = EnvironmentContext()
xp.set_gpucontext(GPUContext.NUMPY)

import numpy as np
if xp._cupy_available:
    import cupy as cp

