import os
import pathlib
import copy
from abc import ABC, abstractmethod

from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QApplication, QFileDialog

from ..environment import GPUContext, proxy
import magicgui

from ..log import logger

class QTModel(QObject):
    
    data_changed = Signal(object)
    
    def __init__(self, data, *args, **kwargs):
        """Initialize the Data object."""
        super().__init__(*args, **kwargs)
        self._data = data
        
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value
        self.data_changed.emit(self._data)
        
    def _copy_from(self, other:'QTModel'):
        self.data = other.data.copy()

    def _deepcopy_from(self, other:'QTModel'):
        self.data = copy.deepcopy(other.data)