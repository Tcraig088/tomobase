
import xarray as xr
from ..core import registers, base_classes

@registers.image_types.register(name="Volume")
class Volume(base_classes.ImageAbstract):
    readers: dict[str, callable] = {}
    writers: dict[str, callable] = {}
    def __init__(self, name, data, pixelsize: float = 1.0, metadata: dict = {}, *args, **kwargs):
        
        if not isinstance(data, xr.DataArray):
            if len(data.shape) == 3:
                dims = ['z', 'y', 'x']
            elif len(data.shape) == 4:
                dims = ['signals', 'z', 'y', 'x']
        super().__init__(name, data, dims, pixelsize, metadata, *args, **kwargs)

    def _copy_from(self, other:'Volume'):
        return super()._copy_from(other=other)
    
    def _deepcopy_from(self, other:'Volume', memo:dict={}):
        return super()._deepcopy_from(other=other, memo=memo)

Volume.readers = {}
Volume.writers = {}