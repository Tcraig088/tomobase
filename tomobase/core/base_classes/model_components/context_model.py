import os
import pathlib
import copy
from abc import ABC, abstractmethod

from ...environment import GPUContext, proxy


from ...log import logger

class ContextModel():
    def __init__(self, data, *args, **kwargs):
        """Initialize the Data object."""
        self.xr = data
        
        self._current_context = None
        self._current_device = None
        
        self.set_context(GPUContext.NUMPY)
        super().__init__(data, *args, **kwargs)
   
    def __getitem__(self, key):
        return self.xr[key]
    
    def __setitem__(self, key, value):
        self.xr[key] = value
        
    def set_context(self, context:GPUContext= GPUContext.NUMPY, device:int = 0):
        logger.trace(f"data type: {type(self.xr)}, current context: {self._current_context}, current device: {self._current_device}, requested context: {context}, requested device: {device}")
        self.xr = proxy.set_array_context(self.xr, self._current_context, self._current_device, context, device)
        self._current_context = context
        self._current_device = device
        logger.debug(f"Set context to {context} on device {device}")
        return self
    
    def get_context(self):
        return self._current_context, self._current_device
    
    @property
    def context(self):
        return self._current_context
    
    @property
    def device(self):
        return self._current_device
    