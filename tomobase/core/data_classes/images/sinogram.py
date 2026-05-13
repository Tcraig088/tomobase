
import numpy as np
import xarray as xr

from ... import registers, base_classes, get_xp

@registers.image_types.register(name="Sinogram")
class Sinogram(base_classes.ImageAbstract):
    _allowed_dims = ['n', 'signals', 'y', 'x']
    
    def __init__(self, name, data, angles: np.ndarray, pixelsize: float = 1.0, times: np.ndarray | None = None, metadata: dict = {}, *args, **kwargs):
                
        data = super()._construct_data_array(data, pixel_size=pixelsize)
        super().__init__(name, data, pixelsize, metadata, *args, **kwargs)

        xp = get_xp(self.xr.data)
        if times is None:
            times_data = xp.arange(self.xr.sizes['n']) + 1
        else:
            times_data = times
        if 'times' not in self.xr.coords or 'angles' not in self.xr.coords:
            len_proj = self.xr.sizes['n']
            self.xr = self.xr.assign_coords(
                n = xp.arange(len_proj),
                times = ('n', times_data),
                angles = ('n', angles)
            )

    def sort(self, by='times'):
        # valid options for by are 'times' 'angles' and 'n'
        if by not in ['times', 'angles', 'n']:
            raise ValueError(f"Invalid sort option {by}. Valid options are 'times', 'angles', and 'n'.")
        self.xr = self.xr.sortby(by)

    def remove(self, n: list[int]):
        self.xr = self.xr.drop_sel(n=n)
        self.removed.emit()
        
    def insert(self, data, axis):
        self.xr = xr.concat([self.xr, data], dim='n')
        self.inserted.emit()

    @property
    def angles(self):
        return self.xr.coords['angles'].values
    
    @angles.setter
    def angles(self, value):
        self.xr.coords["angles"] = ("n", value)

    @property
    def times(self):
        return self.xr.coords['times'].values
    
    @times.setter
    def times(self, value):
        self.xr.coords["times"] = ("n", value)
    
