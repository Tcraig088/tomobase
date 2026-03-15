import os
import pathlib
import copy
from abc import ABC, abstractmethod
import coolname

from qtpy.QtCore import QObject, Slot, Signal
from qtpy.QtWidgets import QApplication, QFileDialog

from ..environment import GPUContext, proxy
import magicgui

from ..log import logger
from .model_components import QTModel, ContextModel, IOModel
import xarray as xr


class BaseDataModel(ContextModel, IOModel, QTModel):
    """Base class for GPU-backed data models with file IO."""
    def __init__(self, name, data, *args, **kwargs):
        """Initialize the Data object."""
        super().__init__(data, *args, **kwargs)
        self.name = name
        
    def _copy_from(self, other:'BaseDataModel'):
        return super()._copy_from(other)
    
    def _deepcopy_from(self, other:'BaseDataModel'):
        return super()._deepcopy_from(other)
    
    def __str__(self):
        
        msg = f"{self.__class__.__name__}:\n"
        msg += f"  Sample Name: {self.name}\n"
        msg += f"  Data Shape: {self.data.shape} Data Type: {self.data.dtype}\n"
        return msg



class ImageAbstract(BaseDataModel):
    
    def __init__(self, name, data, dims, pixel_size=1.0, metadata=None, *args, **kwargs):
        
        if not isinstance(data, xr.DataArray):
            if len(dims) != len(data.shape):
                raise ValueError(f"Number of dimensions in data {len(data.shape)} does not match number of provided dimension names {len(dims)}")
            data = xr.DataArray(data, dims=dims)  
            self.pixel_size = pixel_size 
            for dim in dims:
                if dim in ['x', 'y', 'z']:
                    data.coords[dim] = (data.coords[dim] * pixel_size)
                    data.attrs['pixel_size'] = pixel_size    
                          
        super().__init__(name, data, *args, **kwargs)

        self.metadata = metadata
        self._process_iter =  0 
        
        self.process_name = self._new_process_name()

  
    def _new_process_name(self):
        self._process_iter += 1
        return f"{coolname.generate_slug(2)}_{self._process_iter}"

    @property
    def values(self):
        return self.data.values
    
    def _copy_from(self, other:'ImageAbstract'):
        super()._copy_from(other)
        self.pixel_size = other.pixel_size
        self.process_name = other.process_name
        
    def _deepcopy_from(self, other:'ImageAbstract', memo:dict={}):
        super()._deepcopy_from(other, memo)
        self.pixel_size = other.pixel_size
        self.process_name = other.process_name
       
    def validate(self):
        if not isinstance(self.data, xr.DataArray):
            raise ValueError("Data must be an xarray DataArray or Dataset")
      
    def __str__(self):
        msg = f"{self.__class__.__name__}:\n"
        msg += f"  Sample Name: {self.name}\n"
        msg += f"  Process Name: {self.process_name}\n"
        msg += f"  Data Shape: {self.data.shape} Data Type: {self.data.dtype}\n"
        msg += f"  Pixel Size: {self.pixel_size}\n"
        return msg
    
    def split(self, axis):
        if axis in self.data.dims:
            for i in range(self.data.sizes[axis]):
                yield type(self)._from_dataarray(self.data.isel({axis: i}))
        else:
            raise ValueError(f"Axis {axis} not found in data dimensions {self.data.dims}")
    
    
    def append(self, other:'ImageAbstract', axis):
        if axis in self.data.dims and axis in other.data.dims:
            new_data = xr.concat([self.data, other.data], dim=axis)
            return type(self)._from_dataarray(new_data)
        else:
            raise ValueError(f"Axis {axis} not found in data dimensions {self.data.dims} or {other.data.dims}")  
    
    @classmethod
    def _from_dataarray(cls, dataarray):
        return cls(name=dataarray.name, data=dataarray)
    
    