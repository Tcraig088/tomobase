from abc import abstractmethod
from dataclasses import dataclass
import os
import pathlib
import copy
import coolname
import numpy as np
from qtpy.QtWidgets import QApplication, QFileDialog
from qtpy.QtCore import Signal
import collections
collections.Iterable = collections.abc.Iterable

import xarray as xr
from ..base import BaseDataModel
from ...environment import GPUContext, proxy


@dataclass
class Coordinate:
    name: str
    unit: str
    scale: float = 1.0

class Analysis(BaseDataModel):
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
    
    def __init__(self, name: str=None, description: str = "", axial=False, coords=[], *args, **kwargs):
        """Initialize the Data object

        Args:
            metadata (dict, optional): A dictionary containing metadata about the dataset. Defaults to {}.
        """
        self.name = kwargs.get('name', coolname.generate_slug(2))
        self.description = description 
        self.axial = axial
        _dims = {}
        for coord in coords:
            _dims[coord.name] = proxy.xupy.empty(0.0)
            _units = [coord.unit for coord in coords]
            _scales = [coord.scale for coord in coords]
        if axial:
            _dims['axial'] = proxy.xupy.empty(0.0)
            _units.append('nm')
            _scales.append(1.0)
            
        self._data = xr.DataSet(
            coords=_dims 
        ) 
        for key, value in _dims.items():
            self._data.coords[key].attrs['unit'] = value.attrs['unit']
            self._data.coords[key].attrs['scale'] = value.attrs['scale']
        
            
        super().__init__(*args, **kwargs)
        
        
    @property
    def data(self):
        return self._data
    
    @data.setter
    def data(self, value):
        self._data = value
        self.data_changed.emit(self._data)
        

    def add_data(self, BaseImageModel, **kwaargs):
        
        pass



    def add_axial_data(self, BaseImageModel, **kwaargs):
        pass
    
    
    def __str__(self):
        msg = f"Name: {self.name}, Description: {self.description}"
        return msg
    