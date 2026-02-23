import copy
import pickle
import pathlib
import enum
import json

import numpy as np
import imageio as iio
import pandas as pd


from ...environment import GPUContext, proxy

from .quantification import Quantification

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