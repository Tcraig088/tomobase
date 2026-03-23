from .base import ImageAbstract
import xarray as xr
from ..hooks import image_type_hook

@image_type_hook()
class Image(ImageAbstract):
    def __init__(self, name, data, pixelsize: float = 1.0, metadata: dict = {}, *args, **kwargs):
        
        if not isinstance(data, xr.DataArray):
            if len(data.shape) == 3:
                dims = ['signals', 'y', 'x']
            elif len(data.shape) == 2:
                dims = ['y', 'x']
        super().__init__(name, data, dims, pixelsize, metadata, *args, **kwargs)
    
    def _copy_from(self, other:'Image'):
        return super()._copy_from(other=other)
    
    def _deepcopy_from(self, other:'Image', memo:dict={}):
        return super()._deepcopy_from(other=other, memo=memo)
    
    @classmethod
    def create(cls, name, data, dims, pixel_size=1, metadata=None, *args, **kwargs):
        return cls(name, data, dims, pixel_size, metadata, *args, **kwargs)