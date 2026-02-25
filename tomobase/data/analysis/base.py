
from abc import abstractmethod
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


class BaseAnalysisModel(BaseDataModel):
    """
    Abstract base class for analysis datasets. To implement a child of this class you must:
    
    - implement methods to read data from a file, these should be class methods
      that return an instance of the class

    - implement methods to write data to a file

    - create the class variables ``_readers`` and ``_writers`` which are
      dictionaries that link each supported filetype to the correct reader or
      writer respectively, the keys should be the extensions in lowercase
    
    Attributes:
        metadata (dict): A dictionary containing metadata about the dataset

    """
    
    data_changed = Signal(object)
    
    def __init__(self, name: str=None, description: str = "", *args, **kwargs):
        """Initialize the Data object

        Args:
            metadata (dict, optional): A dictionary containing metadata about the dataset. Defaults to {}.
        """
        self.name = kwargs.get('name', coolname.generate_slug(2))
        self.description = description  
        self.data = None
        super().__init__(*args, **kwargs)
        
        
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value
        self.data_changed.emit(self._data)
        
    @abstractmethod  
    def add_sample(self, sample_name, **kwaargs):
        pass

    def __str__(self):
        msg = f"Name: {self.name}, Description: {self.description}"
        return msg
    