import os
import pathlib
import copy
from abc import ABC, abstractmethod

from ...environment import GPUContext, proxy


from ...log import logger

class ContextModel():
    def __init__(self, data, *args, **kwargs):
        """Initialize the Data object."""
        self._data = data
        
        self._current_context = None
        self._current_device = None
        
        self.set_context(GPUContext.NUMPY)
        super().__init__(data, *args, **kwargs)
   
    def __getitem__(self, key):
        return self._data[key]
    
    def __setitem__(self, key, value):
        self._data[key] = value
        
    def set_context(self, context:GPUContext= GPUContext.NUMPY, device:int = 0):
        self._data = proxy.set_array_context(self.data, self._current_context, self._current_device, context, device)
        self._current_context = context
        self._current_device = device
        logger.debug(f"Set context to {context} on device {device}")

    def get_context(self):
        return self._current_context, self._current_device
    

