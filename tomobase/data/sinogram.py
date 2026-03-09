import os
import glob
import h5py
import numpy as np
import imageio as iio
import copy

from ..environment import proxy
from copy import deepcopy
from scipy.io import savemat, loadmat
import mrcz


from .base import ImageAbstract

import xarray as xr


class Sinogram(ImageAbstract):
    def __init__(self, name, data, angles: np.ndarray, pixelsize: float = 1.0, times: np.ndarray | None = None, metadata: dict = {}, *args, **kwargs):
        
        count = len(data.shape)
        if count == 3:
            dims=['projections', 'x', 'y']
        elif count == 4:
           dims=['projections', 'signals', 'x', 'y']
        else:
            raise ValueError(f"Data should be 3D or 4D, but got {count}D.")
        
        if isinstance(self._data, xr.DataArray):
            # tie angles and times to the projections dimension
            self._data.coords['angles'] = (self._data.coords['projections'], angles)
            if times is not None:
                self._data.coords['times'] = (self._data.coords['projections'], times)
            else:
                self._data.coords['times'] = (self._data.coords['projections'], np.linspace(1, len(angles), len(angles)))
           
        super().__init__(name, data, dims, pixelsize, metadata, *args, **kwargs)
        

        
    