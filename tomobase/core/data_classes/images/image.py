
import xarray as xr

from ... import registers, base_classes

@registers.images.register(name="Image")
class Image(base_classes.ImageAbstract):
    def __init__(self, name, data, pixelsize: float = 1.0, metadata: dict = {}, *args, **kwargs):
        
        data = super()._construct_data_array(data, pixel_size=pixelsize)
        super().__init__(name, data, pixelsize, metadata)
    
