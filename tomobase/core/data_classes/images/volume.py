
import xarray as xr
from ... import registers, base_classes

@registers.images.register(name="Volume")
class Volume(base_classes.ImageAbstract):
    _allowed_dims = ['signals', 'x', 'y', 'z']
    
    def __init__(self, name, data, pixelsize: float = 1.0, metadata: dict = {}, *args, **kwargs):
        
        data = super()._construct_data_array(data, pixel_size=pixelsize)
        super().__init__(name, data, pixelsize, metadata, *args, **kwargs)



