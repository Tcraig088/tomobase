import coolname
import copy

from .components import ContextModel, IOModel, SignalModel
from ...core.environment import get_xp, GPUContext

import xarray as xr




class BaseDataModel(ContextModel, SignalModel, IOModel):
    """Base class for GPU-backed data models with file IO."""
    def __init__(self, name, data, *args, **kwargs):
        """Initialize the Data object."""
        super().__init__(data, *args, **kwargs)
        self.name = name
        
    def __str__(self):
        msg = f"{self.__class__.__name__}:\n"
        msg += f"  Sample Name: {self.name}\n"
        msg += f"  Data Shape: {self.xr.shape} Data Type: {self.xr.dtype}\n"
        return msg


class BaseMeasurementModel(SignalModel, IOModel):
    """Base class for GPU-backed measurement models with file IO."""
    def __init__(self, name, data, *args, **kwargs):
        """Initialize the Measurement object."""
        super().__init__(data, *args, **kwargs)
        self.name = name
        
    def __str__(self):
        msg = f"{self.__class__.__name__}:\n"
        msg += f"  Sample Name: {self.name}\n"
        msg += f"  Data Shape: {self.xr.shape} Data Type: {self.xr.dtype}\n"
        return msg

class ImageAbstract(BaseDataModel):
    _allowed_dims = ('signals', 'x', 'y')
    
    def __init__(self, name, data, pixel_size=1.0, metadata=None, *args, **kwargs):


        super().__init__(name, data, *args, **kwargs)
        self.pixel_size = pixel_size 
        if metadata is not None:
            self.metadata = metadata
        else:
            self.metadata = {}
            
        self._process_id = self._instance_id
        self._process_iter =  0 
        self._process_slug = coolname.generate_slug(2)


    @property
    def signal_labels(self):
        if 'signals' in self.xr.dims:
            return self.xr.coords['signal name'].values
        else:
            return None
        
    @signal_labels.setter
    def signal_labels(self, value):
        if 'signals' in self.xr.dims:
            self.xr.coords['signal name'] = ('signals', value)
    
    def transpose(self, *args):
        for dim in args:
            if dim not in self.xr.dims:
                raise ValueError(f"Dimension {dim} not found in data dimensions {self.xr.dims}")
        
        repositioned_dims = list(args)
        original_index = [self.xr.dims.index(dim) for dim in repositioned_dims]
        sorted_index = sorted(original_index)    

        new_dims = list(self.xr.dims)
        for i, dim in zip(sorted_index, repositioned_dims):            
            new_dims[i] = dim
            
        self.xr = self.xr.transpose(*new_dims)
        return self

    @property
    def spatial_dims(self):
        return [dim for dim in self.xr.dims if dim in ['x', 'y', 'z']]
    
    @property
    def non_spatial_dims(self):
        return [dim for dim in self.xr.dims if dim not in ['x', 'y', 'z']]
    
    @property
    def process_name(self):
        if self._process_id != self._instance_id:
            self._process_id = self._instance_id
            self._process_iter += 1
            self._process_slug = coolname.generate_slug(2)
        return f"{self._process_slug}-{self._process_iter}"

    @property
    def values(self):
        return self.xr.values
    
    @property
    def data(self):
        return self.xr.data
    
    @data.setter
    def data(self, value):
        self.xr.data = value
    
    @property
    def pixel_size(self):
        return self.xr.attrs.get('pixel_size', 1.0)
    
    @pixel_size.setter
    def pixel_size(self, value):
        self.xr.attrs['pixel_size'] = value
        for dim in self.xr.dims:
            if dim in ['x', 'y', 'z']:
                self.xr.coords[dim] = (self.xr.coords[dim] * value)


    @property
    def metadata(self):
        return self.xr.attrs.get('metadata', None)
    
    @metadata.setter
    def metadata(self, value):
        self.xr.attrs['metadata'] = value
        
    def __str__(self):
        msg = f"{self.__class__.__name__}:\n"
        msg += f"  Sample Name: {self.name}\n"
        msg += f"  Process Name: {self.process_name}\n"
        msg += f"  Data Shape: {self.xr.shape} Data Type: {self.xr.dtype}\n"
        msg += f"  Pixel Size: {self.pixel_size}\n"
        return msg
    
    def split(self, axis):
        if axis in self.xr.dims:
            for i in range(self.xr.sizes[axis]):
                yield type(self)._from_dataarray(self.name, self.xr.isel({axis: i})).set_context(self.context, self.device)
        else:
            raise ValueError(f"Axis {axis} not found in data dimensions {self.xr.dims}")
    
    
    def append(self, other:'ImageAbstract', axis):
        if issubclass(type(other), type(ImageAbstract)):
            xr = other.xr
        else: 
            xr = other

        if axis in self.xr.dims and axis in xr.dims:
            self.xr = xr.concat([self.xr, xr], dim=axis)
            return self
        else:
            raise ValueError(f"Axis {axis} not found in data dimensions {self.xr.dims} or {xr.dims}")  
    
    def insert(self):
        self.added.emit()
        
    def remove(self):
        self.removed.emit()
    
    
    @classmethod
    def _construct_data_array(cls, data, pixel_size=1.0):
        if isinstance(data, xr.DataArray):
            raise ValueError("Data must base a base array for initial construction of data array. E.g. numpy array, cupy array, dask array, etc.")
            
        dims = list(cls._allowed_dims)
        if len(cls._allowed_dims) > len(data.shape):
            dims.remove('signals')
            
        if len(dims) != len(data.shape):
            raise ValueError(f"Number of dimensions in data {len(data.shape)} does not match number of provided dimension names {len(dims)}")
        
        data = xr.DataArray(data, dims=dims)
        for dim in dims:
            if dim in ['x', 'y', 'z']:
                data.coords[dim] = (data.coords[dim] * pixel_size)  
        return data
    
    @classmethod
    def _from_dataarray(cls, name, data:xr.DataArray):
        obj = cls.__new__(cls)
        ImageAbstract.__init__(obj, name=name, data=data, pixel_size=data.attrs.get('pixel_size', 1.0), metadata=data.attrs.get('metadata', None))
        return obj
    
    @classmethod
    def array_like(cls, other:'ImageAbstract', values=0.0,**kwargs):
        xp = get_xp(other.xr.data)

        dims = {}
        for dim in other.xr.dims:
            if dim in cls._allowed_dims:
                dims[dim] = other.xr.sizes[dim]
        for key, value in kwargs.items():
            if key in cls._allowed_dims:
                dims[key] = value
                
        
        sorted_dims = dict(sorted(dims.items(), key=lambda item: cls._allowed_dims.index(item[0])))
        dims_shape = list(sorted_dims.values())
        dims = list(sorted_dims.keys())
        
        data = xr.DataArray(xp.full(tuple(dims_shape), values), dims=dims)
        data.attrs['pixel_size'] = other.pixel_size
        data.attrs['metadata'] = other.metadata
        
        return cls._from_dataarray(other.name, data)
    
    def reshape_and_fill(self, data, coords=None):
        if data.ndim != self.xr.ndim:
            raise ValueError(
                f"Data ndim {data.ndim} does not match existing ndim {self.xr.ndim}"
            )

        old = self.xr

        if coords is None:
            coords = {}

            for name, coord in old.coords.items():
                # Preserve scalar coords
                if coord.ndim == 0:
                    coords[name] = coord
                    continue

                # Preserve coords whose dimensions still exist
                if all(dim in old.dims for dim in coord.dims):
                    same_shape = all(
                        old.sizes[dim] == data.shape[old.get_axis_num(dim)]
                        for dim in coord.dims
                    )

                    if same_shape:
                        coords[name] = coord

        self.xr = xr.DataArray(
            data,
            dims=old.dims,
            coords=coords,
            attrs=old.attrs.copy(),
            name=old.name,
        )

        return self
    
    
class MeasurementAbstract(BaseMeasurementModel):
    def __init__(self, name, data, metadata=None, *args, **kwargs):
        super().__init__(name, data, *args, **kwargs)
