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

class PointMap(BaseAnalysisModel):
    ''' A simple analysis model for storing point-based measurements. The data is stored in a pandas DataFrame with columns for the name of the measurement, 
    the value, and optional error bars. The class also includes metadata such as units and title. The data can be saved to and loaded from .dat files using JSON serialization.'''
    def __init__(self, name, description: str = "", units="a.u.", axis_title="", *args, **kwargs):
        super().__init__(name=name, description=description)
        self.data = pd.DataFrame(columns=['name', 'process_name', 'process', 'y', 'y_error+', 'y_error-'])
        self.units = units
        self.axis_title = axis_title
        
    def add_data(self, image:BaseImageModel, value, plus_error=np.nan, minus_error=np.nan):
        new_df = pd.DataFrame({'name': [image.sample_name], 'process_name': [image.process_name], 'process': [image.process_name], 'y': [value], 'y_error+': [plus_error], 'y_error-': [minus_error]})
        self.data = pd.concat([self.data, new_df], ignore_index=True)

    def _write_h5(self, filename: pathlib.Path, **kwargs):
        """Writer for .h5 files."""
        filename = pathlib.Path(filename)
        with h5py.File(filename, "w") as f:
            f.create_dataset("data", data=self.data.to_numpy(), compression="gzip")
            f.attrs["columns"] = json.dumps(self.data.columns.tolist())
            f.attrs["units"] = self.units
            f.attrs["axis_title"] = self.axis_title
            f.attrs["description"] = self.description


    @classmethod
    def _read_h5(cls, filename: pathlib.Path, **kwargs) -> "PointMap":
        """Reader for .h5 files, returns a PointMap instance."""
        filename = pathlib.Path(filename)
        with h5py.File(filename, "r") as f:
            data_array = f["data"][:]
            columns = json.loads(f.attrs["columns"])
            data_df = pd.DataFrame(data_array, columns=columns)
            units = f.attrs.get("units", "a.u.")
            axis_title = f.attrs.get("axis_title", "")
            description = f.attrs.get("description", "")
        
        obj = cls(name=filename.stem, description=description, units=units, axis_title=axis_title)
        obj.data = data_df
        return obj
    
PointMap.readers['h5'] = PointMap._read_h5
PointMap.writers['h5'] = PointMap._write_h5

'''
class PointMap(Quantification):
    def __init__(self, name, value, description: str = "", units="a.u.", title="", *args, **kwargs):
        self.data = pd.DataFrame(columns=['name', 'y', 'y_error+', 'y_error-'])
        self.units = units
        self.title = title

        super().__init__(description=description)

    def add_data(self, name, value):
        if isinstance(value, tuple):
            new_df = pd.DataFrame({'name': [name], 'y': [value[0]], 'y_error+': [value[1]], 'y_error-': [value[2]]})
        else:
            new_df = pd.DataFrame({'name': [name], 'y': [value], 'y_error+': [np.nan], 'y_error-': [np.nan]})
        
        self.data = pd.concat([self.data, new_df], ignore_index=True)
            

    def set_context(self, context: GPUContext | None = None, device: int | None = None):
        super().set_context(context=context, device=device)

    def __str__(self):
        msg = f"Quantification (PointMap)\n"
        msg += f"  {self.title} (Units: ){self.units})\n"
        msg += f"  Description: {self.description}\n"
        msg += f"  Data: {self.data['name'].tolist()}\n"
        return msg

    def _copy_from(self, other: "PointMap"):
        """Shallow copy of payload (data/metadata/qtype/description)."""
        self.data = other.data
        self.units = other.units
        self.title = other.title
        super()._copy_from(other)

    def _deepcopy_from(self, other: "PointMap", memo: dict):
        """Deep copy of payload (data/metadata/qtype/description)."""
        self.data = copy.deepcopy(other.data, memo)
        self.units = copy.deepcopy(other.units, memo)
        self.title = copy.deepcopy(other.title, memo)
        super()._deepcopy_from(other, memo)

    def _write_dat(self, filename: pathlib.Path, **kwargs):
        """Writer for .dat files (pickle of internal state)."""
        state = {
            "data": self.data.to_dict(),
            "units": self.units,
            "title": self.title,        
            "description": self.description
        }
        filename = pathlib.Path(filename)
        with filename.open("w") as f:
            json.dump(state, f, indent=4)

    @classmethod
    def _read_dat(cls, filename: pathlib.Path, **kwargs) -> "PointMap":
        """Reader for .dat files, returns a Quantification instance."""
        filename = pathlib.Path(filename)
        with filename.open("r") as f:
            state = json.load(f)
     
        obj = cls.__init__(name=state["names"], 
                            map=state["data"], 
                            description=state["description"],
                            units=state["units"],
                            title=state["title"])
    
        return obj

Heatmap._readers['dat'] = Heatmap._read_dat

Heatmap._writers['dat'] = Heatmap._write_dat
'''