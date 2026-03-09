import os
import pathlib
import copy
import coolname
import numpy as np
from qtpy.QtWidgets import QApplication, QFileDialog
from qtpy.QtCore import Signal
import collections
collections.Iterable = collections.abc.Iterable

from ..base import BaseDataModel

from ...log import logger
from ...environment import GPUContext, proxy

class Image(BaseDataModel):
    """
    Abstract base class for microscopy and tomography datasets. To implement a child of this class you must:
    
    - implement methods to read data from a file, these should be class methods
      that return an instance of the class

    - implement methods to write data to a file

    - create the class variables ``_readers`` and ``_writers`` which are
      dictionaries that link each supported filetype to the correct reader or
      writer respectively, the keys should be the extensions in lowercase
    
    Attributes:
        pixelsize (float): The size of the pixels in the dataset
        metadata (dict): A dictionary containing metadata about the dataset

    """
    data_changed = Signal(object)

    def __init__(self, data, pixelsize: float=1.0, metadata: dict = {}, *args, **kwargs):
        """Initialize the Data object

        Args:
            pixelsize (float, optional): The size of the pixels in the dataset. Defaults to 1.0 nm
            metadata (dict, optional): A dictionary containing metadata about the dataset. Defaults to {}.
        """
        self.sample_name = kwargs.get('sample_name', coolname.generate_slug(2))
        self.process_name = kwargs.get('process_name', coolname.generate_slug(2))
        self._data = data
        self.pixelsize = pixelsize
        self.metadata = metadata
        super().__init__(*args, **kwargs)
    
    
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value
        self.data_changed.emit(self._data)
    
    def set_context(self, context:GPUContext | None = None, device:int | None = None):
        super().set_context(context, device)
        self.data = proxy.asarray(self.data, context, device)

    def _copy_from(self, other:'Image'):
        """Copy data from another BaseImageModel instance

        Args:
            other (BaseImageModel): The instance to copy from
        """
        self.data = other.data.copy()
        self.pixelsize = other.pixelsize
        self.metadata = copy.deepcopy(other.metadata)
        
    def _deepcopy_from(self, other='BaseImageModel', memo:dict={}):
        self.sample_name = other.sample_name
        self.process_name = other.process_name
        self.data = copy.deepcopy(other.data, memo)
        self.pixelsize = other.pixelsize
        self.metadata = copy.deepcopy(other.metadata, memo)
        
    
    def __str__(self):
        
        msg = f"{self.__class__.__name__}:\n"
        msg += f"  Sample Name: {self.sample_name}\n"
        msg += f"  Process Name: {self.process_name}\n"
        msg += f"  Data Shape: {self.data.shape}\n"
        msg += f"  Pixelsize: {self.pixelsize}\n"
        msg += f"  Metadata:\n"
        for key, value in self.metadata.items():
            logger.info(f"Metadata: {key} : {value}")
        return msg
