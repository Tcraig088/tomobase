import coolname

from .model_components import ContextModel, IOModel, SignalModel

import xarray as xr


'''
    def _copy_from(self, other:'BaseDataModel'):
        return super()._copy_from(other)
    
    def _deepcopy_from(self, other:'BaseDataModel'):
        return super()._deepcopy_from(other)
'''


class BaseDataModel(ContextModel, SignalModel, IOModel):
    """Base class for GPU-backed data models with file IO."""
    def __init__(self, name, data, *args, **kwargs):
        """Initialize the Data object."""
        super().__init__(data, *args, **kwargs)
        self.name = name
        
    def __str__(self):
        msg = f"{self.__class__.__name__}:\n"
        msg += f"  Sample Name: {self.name}\n"
        msg += f"  Data Shape: {self.data.shape} Data Type: {self.data.dtype}\n"
        return msg

class ImageAbstract(BaseDataModel):
    def __init__(self, name, data, dims=None, pixel_size=1.0, metadata=None, *args, **kwargs):
        
        if not isinstance(data, xr.DataArray):
            if len(dims) != len(data.shape):
                raise ValueError(f"Number of dimensions in data {len(data.shape)} does not match number of provided dimension names {len(dims)}")
            data = xr.DataArray(data, dims=dims)  

            for dim in dims:
                if dim in ['x', 'y', 'z']:
                    data.coords[dim] = (data.coords[dim] * pixel_size)  
            
        super().__init__(name, data, *args, **kwargs)
        self.pixel_size = pixel_size 
        self.metadata = metadata
        self._process_iter =  0 
        
        self.process_name = self._new_process_name()

  
    def _new_process_name(self):
        self._process_iter += 1
        return f"{coolname.generate_slug(2)}_{self._process_iter}"

    @property
    def values(self):
        return self.data.values
    
    @property
    def pixel_size(self):
        return self._data.attrs.get('pixel_size', 1.0)
    
    @pixel_size.setter
    def pixel_size(self, value):
        self._data.attrs['pixel_size'] = value
        for dim in self.data.dims:
            if dim in ['x', 'y', 'z']:
                self.data.coords[dim] = (self.data.coords[dim] * value)

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
        if issubclass(type(other), type(ImageAbstract)):
            data = other.data
        else: 
            data = other

        if axis in self.data.dims and axis in data.dims:
            self.data = xr.concat([self.data, data], dim=axis)
            return self
        else:
            raise ValueError(f"Axis {axis} not found in data dimensions {self.data.dims} or {data.dims}")  
    
    def insert(self):
        self.added.emit()
        
    def remove(self):
        self.removed.emit()
    
    @classmethod
    def _from_dataarray(cls, dataarray):
        return cls(name=dataarray.name, data=dataarray)
    

    
    