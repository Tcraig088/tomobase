import os
import pathlib
import copy
from abc import ABC, abstractmethod

from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QApplication, QFileDialog

from ..environment import GPUContext, proxy
import magicgui

from ..log import logger

class ContextModel():
    def __init__(self, data, *args, **kwargs):
        """Initialize the Data object."""
        self._data = data
        
        self._current_context = None
        self._current_device = None
        
        self.set_context(GPUContext.NUMPY)
   
    def set_context(self, context:GPUContext= GPUContext.NUMPY, device:int = 0):
        self._data = proxy.set_array(self.data, context, device)
        self._current_context = context
        self._current_device = device
        logger.debug(f"Set context to {context} on device {device}")

    def get_context(self):
        return self._current_context, self._current_device

