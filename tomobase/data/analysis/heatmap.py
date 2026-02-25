import copy
import pickle
import pathlib
import enum
import json
import h5py

import numpy as np
import imageio as iio
import pandas as pd


from ...environment import GPUContext, proxy

from ..images.base import BaseImageModel
from .base import BaseAnalysisModel

class Heatmap(BaseAnalysisModel):
    ''' A simple analysis model for storing point-based measurements. The data is stored in a pandas DataFrame with columns for the name of the measurement, 
    the value, and optional error bars. The class also includes metadata such as units and title. The data can be saved to and loaded from .dat files using JSON serialization.'''
    def __init__(self, name, description: str = "", units_x="a.u.", units_y="a.u.", units_z="a.u.", x_axis_title="", y_axis_title="", z_axis_title="", pixelsize_x=1.0, pixelsize_y=1.0, *args, **kwargs):
        super().__init__(name=name, description=description)
        self.data = {}
        self.units_x = units_x
        self.units_y = units_y
        self.units_z = units_z
        self.x_axis_title = x_axis_title
        self.y_axis_title = y_axis_title
        self.z_axis_title = z_axis_title
        
        self.pixelsize_x = pixelsize_x
        self.pixelsize_y = pixelsize_y
        
    def add_data(self, image:BaseImageModel, value, plus_error=None, minus_error=None):
        if image.process_name not in self.data:
            self.data[image.process_name] = {}
        self.data[image.process_name][image.sample_name] = value
        self.data[value] = value
        
        if plus_error is not None:
            self.data[image.process_name]['plus_error'] = plus_error
        if minus_error is not None:
            self.data[image.process_name]['minus_error'] = minus_error

    def _write_h5(self, filename: pathlib.Path, **kwargs):
        """Writer for .h5 files."""
        filename = pathlib.Path(filename)
        with h5py.File(filename, "w") as f:
            f.create_dataset("data", data=json.dumps(self.data), compression="gzip")
            f.attrs["units_x"] = self.units_x
            f.attrs["units_y"] = self.units_y
            f.attrs["units_z"] = self.units_z
            f.attrs["x_axis_title"] = self.x_axis_title
            f.attrs["y_axis_title"] = self.y_axis_title
            f.attrs["z_axis_title"] = self.z_axis_title
            f.attrs["pixelsize_x"] = self.pixelsize_x
            f.attrs["pixelsize_y"] = self.pixelsize_y
            f.attrs["description"] = self.description
            


    @classmethod
    def _read_h5(cls, filename: pathlib.Path, **kwargs):
        """Reader for .h5 files, returns a PointMap instance."""
        filename = pathlib.Path(filename)
        with h5py.File(filename, "r") as f:
            data = json.loads(f["data"][:].tobytes().decode("utf-8"))
            units_x = f.attrs.get("units_x", "a.u.")
            units_y = f.attrs.get("units_y", "a.u.")
            units_z = f.attrs.get("units_z", "a.u.")
            x_axis_title = f.attrs.get("x_axis_title", "")
            y_axis_title = f.attrs.get("y_axis_title", "")
            z_axis_title = f.attrs.get("z_axis_title", "")
            pixelsize_x = f.attrs.get("pixelsize_x", 1.0)
            pixelsize_y = f.attrs.get("pixelsize_y", 1.0)
            description = f.attrs.get("description", "")
        
        obj = cls(name=filename.stem, description=description, units_x=units_x, units_y=units_y, units_z=units_z,
                  x_axis_title=x_axis_title, y_axis_title=y_axis_title, z_axis_title=z_axis_title,
                  pixelsize_x=pixelsize_x, pixelsize_y=pixelsize_y)
        obj.data = data
        return obj
    
Heatmap.readers['h5'] = Heatmap._read_h5
Heatmap.writers['h5'] = Heatmap._write_h5