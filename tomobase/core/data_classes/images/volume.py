
import xarray as xr
from ... import registers, base_classes

@registers.image_types.register(name="Volume")
class Volume(base_classes.ImageAbstract):
    readers: dict[str, callable] = {}
    writers: dict[str, callable] = {}
    renderer = None

    def __init__(self, name, data, pixelsize: float = 1.0, metadata: dict = {}, *args, **kwargs):
        
        if not isinstance(data, xr.DataArray):
            if len(data.shape) == 3:
                dims = ['x', 'y', 'z']
            elif len(data.shape) == 4:
                dims = ['signals', 'x', 'y', 'z']
        super().__init__(name, data, dims, pixelsize, metadata, *args, **kwargs)

    def show(self, verbose=True, **kwargs):
        if self.renderer is None:
            raise Exception("Must Enable Jupyter Backend to show volume data.")
        self.renderer.show(self, verbose)

Volume.readers = {}
Volume.writers = {}