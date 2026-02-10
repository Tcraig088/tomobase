import copy
import pickle
import pathlib
import enum

import numpy as np
import imageio as iio
import pandas as pd

from ...registrations.datatypes import image_datatypes_register
from ...registrations.environment import GPUContext, proxy

from ..base import BaseDataModel


class QuantificationType(enum.Enum):
    HEAT_MAP = 1
    VALUE = 2
    PROJECTION_MAP = 3
    XY_MAP = 4


class Quantification(BaseDataModel):
    """
    Quantification data model with several qtypes and metadata.
    """

    # file IO (populated after class body)
    readers: dict[str, callable] = {}
    writers: dict[str, callable] = {}

    def __init__(self, qtype: QuantificationType, description: str = "", *args, **kwargs):
        self._data = None
        self._init = False
        self._metadata = {}
        self._description = description
        self._qtype = qtype

        # First call should set things up; your logic here looks inverted,
        # but I'll keep it as you wrote it (you can flip _init semantics later).
        self._init = True

        match qtype:
            case QuantificationType.HEAT_MAP:
                self.add_heatmap_data(*args, **kwargs)
            case QuantificationType.VALUE:
                self.add_value(*args, **kwargs)
            case QuantificationType.PROJECTION_MAP:
                # nothing yet
                pass
            case QuantificationType.XY_MAP:
                self.add_xy_map(*args, **kwargs)
            case _:
                raise ValueError("Quantification type not recognized.")

        # After initial construction, consider object initialized
        self._init = False

        super().__init__()

    # ------------------------------------------------------------------ #
    # Data adders (unchanged except for minor comments)
    # ------------------------------------------------------------------ #

    def add_heatmap_data(
        self,
        name,
        map,
        x_units="a.u.",
        y_units="a.u.",
        x_scale=1.0,
        y_scale=1.0,
        x_title="",
        y_title="",
        *args,
        **kwargs,
    ):
        if self._qtype != QuantificationType.HEAT_MAP:
            raise ValueError("Quantification type is not HEAT_MAP.")
        if self._init:
            self.data = np.zeros(map.shape)
            self._metadata["names"] = []
            self._metadata["x_units"] = x_units
            self._metadata["y_units"] = y_units
            self._metadata["x_scale"] = x_scale
            self._metadata["y_scale"] = y_scale
            self._metadata["x_title"] = x_title
            self._metadata["y_title"] = y_title

        if len(self._metadata.get("names", [])) == 0:
            self.data = map
            self._metadata["names"] = [name]
        else:
            self.data = np.concatenate((self.data, map), axis=2)
            self._metadata["names"].append(name)

    def add_value(
        self,
        name,
        value,
        units="a.u.",
        y_title="",
        *args,
        **kwargs,
    ):
        if self._qtype != QuantificationType.VALUE:
            raise ValueError("Quantification type is not VALUE.")

        if self._init:
            self.data = pd.DataFrame(columns=["name", "value"])
            self._metadata["units"] = units
            self._metadata["y_title"] = y_title

        new_entry = pd.DataFrame({"name": [name], "value": [value]})
        self.data = pd.concat([self.data, new_entry], ignore_index=True)

    def add_xy_map(
        self,
        name,
        x,
        y,
        x_units="a.u.",
        y_units="a.u.",
        x_title="",
        y_title="",
        x_error=None,
        y_error=None,
        *args,
        **kwargs,
    ):
        if self._qtype != QuantificationType.XY_MAP:
            raise ValueError("Quantification type is not XY_MAP.")

        if self._init:
            self.data = pd.DataFrame()
            self._metadata["x_units"] = x_units
            self._metadata["y_units"] = y_units
            self._metadata["x_title"] = x_title
            self._metadata["y_title"] = y_title

        new_entry = pd.DataFrame({name + "_x": x, name + "_y": y})
        if x_error is not None:
            new_entry[name + "_x_error"] = x_error
        if y_error is not None:
            new_entry[name + "_y_error"] = y_error
        self.data = pd.concat([self.data, new_entry], axis=1)

    def add_projection_map(
        self,
        sino,
        y,
        y_units="a.u.",
        y_title="",
        y_error=None,
        *args,
        **kwargs,
    ):
        if self._qtype != QuantificationType.PROJECTION_MAP:
            raise ValueError("Quantification type is not PROJECTION_MAP.")

        if self._init:
            self.data = pd.DataFrame()
            self._metadata["y_units"] = y_units
            self._metadata["y_title"] = y_title

        new_entry = pd.DataFrame(
            {
                sino.pname + "_angles": sino.angles,
                sino.pname + "_times": sino.times,
                sino.pname + "_y": y,
            }
        )
        if y_error is not None:
            new_entry[sino.pname + "_y_error"] = y_error
        self.data = pd.concat([self.data, new_entry], axis=1)

    # ------------------------------------------------------------------ #
    # Context + representation
    # ------------------------------------------------------------------ #

    def set_context(self, context: GPUContext | None = None, device: int | None = None):
        # just delegate to BaseDataModel’s logic
        super().set_context(context=context, device=device)

    def __str__(self):
        # `self.name` was not defined anywhere, so I’ll just use description
        return f"Quantification({self._qtype.name}, description={self._description!r})"

    # ------------------------------------------------------------------ #
    # Copy / deepcopy hooks for BaseDataModel
    # ------------------------------------------------------------------ #

    def _copy_from(self, other: "Quantification"):
        """Shallow copy of payload (data/metadata/qtype/description)."""
        self._data = other._data           # shared reference
        self._metadata = other._metadata   # shared dict (shallow)
        self._description = other._description
        self._qtype = other._qtype
        self._init = other._init

    def _deepcopy_from(self, other: "Quantification", memo: dict):
        """Deep copy of payload."""
        self._data = copy.deepcopy(other._data, memo)
        self._metadata = copy.deepcopy(other._metadata, memo)
        self._description = copy.deepcopy(other._description, memo)
        # Enum is immutable; shallow copy is fine
        self._qtype = other._qtype
        self._init = other._init

    # ------------------------------------------------------------------ #
    # .dat IO (pickle-based)
    # ------------------------------------------------------------------ #

    def _write_dat(self, filename: pathlib.Path, **kwargs):
        """Writer for .dat files (pickle of internal state)."""
        state = {
            "qtype": self._qtype.name,     # store name for robustness
            "description": self._description,
            "metadata": self._metadata,
            "data": self._data,
        }
        filename = pathlib.Path(filename)
        with filename.open("wb") as f:
            pickle.dump(state, f, protocol=pickle.HIGHEST_PROTOCOL)

    @classmethod
    def _read_dat(cls, filename: pathlib.Path, **kwargs) -> "Quantification":
        """Reader for .dat files, returns a Quantification instance."""
        filename = pathlib.Path(filename)
        with filename.open("rb") as f:
            state = pickle.load(f)

        # Bypass __init__ to avoid re-running add_* logic
        obj = cls.__new__(cls)

        # Initialise BaseDataModel part
        BaseDataModel.__init__(obj)

        # Restore fields
        qtype = QuantificationType[state["qtype"]]
        obj._qtype = qtype
        obj._description = state["description"]
        obj._metadata = state["metadata"]
        obj._data = state["data"]
        obj._init = False  # already fully initialised

        return obj
