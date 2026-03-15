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
    readers: dict[str, callable] = {}
    writers: dict[str, callable] = {}
    def __init__(self, name, data, angles: np.ndarray, pixelsize: float = 1.0, times: np.ndarray | None = None, metadata: dict = {}, *args, **kwargs):
        
        count = len(data.shape)
        if count == 3:
            dims=['projections', 'y', 'x']
        elif count == 4:
           dims=['projections', 'signals', 'y', 'x']
        else:
            raise ValueError(f"Data should be 3D or 4D, but got {count}D.")
        
        super().__init__(name, data, dims, pixelsize, metadata, *args, **kwargs)
        # check angles and times are coords of the data


        #if times and angles are not already coordinates, assign them as coordinates
        if 'times' not in self._data.coords or 'angles' not in self._data.coords:
            xp = self._data.values.__array_namespace__()
            len_proj = self._data.sizes['projections']
            self._data.assign_coords(
                projections = xp.arange(len_proj),
                times = ('projections', times) if times is not None else xp.arange(len_proj)+1,
                angles = ('projections', angles)
            )

    def _copy_from(self, other:'Sinogram'):
        return super()._copy_from(other)
    
    def _deepcopy_from(self, other:'Sinogram', memo:dict={}):
        return super()._deepcopy_from(other, memo)
    
    def sort(self, by='times'):
        # valid options for by are 'times' 'angles' and 'projections'
        if by not in ['times', 'angles', 'projections']:
            raise ValueError(f"Invalid sort option {by}. Valid options are 'times', 'angles', and 'projections'.")
        self.data = self.data.sortby(by)

    def remove(self, projections: list[int]):
        self.data = self.data.drop_sel(projections=projections)

Sinogram.readers = {}
Sinogram.writers = {}