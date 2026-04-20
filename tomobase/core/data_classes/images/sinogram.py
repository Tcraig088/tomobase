
import numpy as np
import xarray as xr

from ... import registers, base_classes

@registers.image_types.register(name="Sinogram")
class Sinogram(base_classes.ImageAbstract):
    def __init__(self, name, data, angles: np.ndarray, pixelsize: float = 1.0, times: np.ndarray | None = None, metadata: dict = {}, *args, **kwargs):
        
        count = len(data.shape)
        if count == 3:
            dims=['n', 'y', 'x']
        elif count == 4:
           dims=['projections', 'signals', 'y', 'x']
        else:
            raise ValueError(f"Data should be 3D or 4D, but got {count}D.")
        
        super().__init__(name, data, dims, pixelsize, metadata, *args, **kwargs)
        # check angles and times are coords of the data


        #if times and angles are not already coordinates, assign them as coordinates
        xp = self._data.values.__array_namespace__()
        
        if times is None:
            times_data = xp.arange(self._data.sizes['n']) + 1
        else:
            times_data = times
        if 'times' not in self._data.coords or 'angles' not in self._data.coords:
            len_proj = self._data.sizes['n']
            self._data = self._data.assign_coords(
                n = xp.arange(len_proj),
                times = ('n', times_data),
                angles = ('n', angles)
            )

    def sort(self, by='times'):
        # valid options for by are 'times' 'angles' and 'n'
        if by not in ['times', 'angles', 'n']:
            raise ValueError(f"Invalid sort option {by}. Valid options are 'times', 'angles', and 'n'.")
        self.data = self.data.sortby(by)

    def remove(self, n: list[int]):
        self.data = self.data.drop_sel(n=n)
        self.removed.emit()
        
    def insert(self, data, axis):
        self.data = xr.concat([self.data, data], dim='n')
        self.inserted.emit()

    @property
    def angles(self):
        return self.data.coords['angles'].values
    
    @angles.setter
    def angles(self, value):
        self.data.coords['angles'] = value

    @property
    def times(self):
        return self.data.coords['times'].values
    
    @times.setter
    def times(self, value):
        self.data.coords['times'] = value
    
