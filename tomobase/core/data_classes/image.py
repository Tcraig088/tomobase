
import xarray as xr

from .. import registers, base_classes

@registers.image_types.register(name="Image")
class Image(base_classes.ImageAbstract):
    def __init__(self, name, data, pixelsize: float = 1.0, metadata: dict = {}, *args, **kwargs):
        
        if not isinstance(data, xr.DataArray):
            if len(data.shape) == 3:
                dims = ['signals', 'y', 'x']
            elif len(data.shape) == 2:
                dims = ['y', 'x']
        super().__init__(name, data, dims, pixelsize, metadata, *args, **kwargs)
    
