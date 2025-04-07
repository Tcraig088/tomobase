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
    

    def __getattr__(self, name):
        if self.context == GPUContext.CUPY and self._cupy_available:
            module = cp
        else:
            module = np
                
        attr = getattr(module, name)
        if name != 'get_context' and name != 'set_context' and name != '__getattr__':
            if callable(attr):
                def wrapper(*args, **kwargs):
                    return attr(*args, **kwargs)
                return wrapper
            else:
                return attr
            
    def get_context(self):
        _dict = {}
        _dict['context'] = self.context
        _dict['device'] = self.device
        return _dict

import numpy as np
xp = EnvironmentContext()
xp.set_context(GPUContext.NUMPY)
if xp._cupy_available:
    import cupy as cp

