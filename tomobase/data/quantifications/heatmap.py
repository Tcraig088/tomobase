import copy
import pickle
import pathlib
import enum
import json

import numpy as np
import imageio as iio
import pandas as pd

from ...registrations.environment import GPUContext, proxy

from .quantification import Quantification


class Heatmap(Quantification):
    def __init__(self, name, map, description: str = "", x_units="a.u.", y_units="a.u.", x_scale=1.0, y_scale=1.0, x_title="", y_title="", *args, **kwargs):
        self.data = map
        self.names = [name]
        self.x_units = x_units
        self.y_units = y_units
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.x_title = x_title
        self.y_title = y_title

        super().__init__(description=description)

    def add_data(self,name,map):
        if len(self.names) == 0:
            self.data = map
            self.names = [name]
        else:
            self.data = np.concatenate((self.data, map), axis=2)
            self.names.append(name)

    def set_context(self, context: GPUContext | None = None, device: int | None = None):
        super().set_context(context=context, device=device)

    def __str__(self):
        msg = f"Quantification (Heatmap)\n"
        msg += f"  Description: {self.description}\n"
        msg += f"  Data Sets: {self.names}\n"
        msg += f"  Data Shape: {self.data.shape}\n"
        msg += f"  [X] {self.x_title} Units: {self.x_units}, Scale: {self.x_scale}\n"
        msg += f"  [Y] {self.y_title} Units: {self.y_units}, Scale: {self.y_scale}\n"
        return msg

    def _copy_from(self, other: "Heatmap"):
        """Shallow copy of payload (data/metadata/qtype/description)."""
        self.data = other.data           
        self.names = other.names          
        self.x_units = other.x_units
        self.y_units = other.y_units
        self.x_scale = other.x_scale
        self.y_scale = other.y_scale
        self.x_title = other.x_title
        self.y_title = other.y_title
        super()._copy_from(other)

    def _deepcopy_from(self, other: "Heatmap", memo: dict):
        """Deep copy of payload (data/metadata/qtype/description)."""
        self.data = copy.deepcopy(other.data, memo)
        self.names = copy.deepcopy(other.names, memo)
        self.x_units = copy.deepcopy(other.x_units, memo)
        self.y_units = copy.deepcopy(other.y_units, memo)
        self.x_scale = copy.deepcopy(other.x_scale, memo)
        self.y_scale = copy.deepcopy(other.y_scale, memo)
        self.x_title = copy.deepcopy(other.x_title, memo)
        self.y_title = copy.deepcopy(other.y_title, memo)
        super()._deepcopy_from(other, memo)

    def _write_dat(self, filename: pathlib.Path, **kwargs):
        """Writer for .dat files (pickle of internal state)."""
        state = {
            "data": self.data,
            "names": self.names,
            "x_units": self.x_units,
            "y_units": self.y_units,
            "x_scale": self.x_scale,
            "y_scale": self.y_scale,
            "x_title": self.x_title,
            "y_title": self.y_title,
            "description": self.description
        }
        filename = pathlib.Path(filename)
        with filename.open("w") as f:
            json.dump(state, f, indent=4)

    @classmethod
    def _read_dat(cls, filename: pathlib.Path, **kwargs) -> "Heatmap":
        """Reader for .dat files, returns a Quantification instance."""
        filename = pathlib.Path(filename)
        with filename.open("r") as f:
            state = json.load(f)
     
        obj = cls.__init__(name=state["names"], 
                            map=state["data"], 
                            description=state["description"],
                            x_units=state["x_units"],
                            y_units=state["y_units"],
                            x_scale=state["x_scale"],
                            y_scale=state["y_scale"],
                            x_title=state["x_title"],
                            y_title=state["y_title"])
    
        return obj

Heatmap._readers['dat'] = Heatmap._read_dat

Heatmap._writers['dat'] = Heatmap._write_dat