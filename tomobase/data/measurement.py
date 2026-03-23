from dataclasses import dataclass
import collections
collections.Iterable = collections.abc.Iterable

import xarray as xr

from ..core import base_classes


@dataclass
class Coordinate:
    name: str
    unit: str = 'a.u.'
    scale: float = 1.0

class Measurement(base_classes.BaseDataModel):
    def __init__(self, name, dims, metadata=None, *args, **kwargs):
        sample = Coordinate(name="sample", unit="a.u.", scale=1.0)
        dims = [sample] + dims

        # empty coordinates: each dimension starts with length 0
        coords = {
            dim.name: xr.DataArray([], dims=(dim.name,), attrs={
                "unit": dim.unit,
                "scale": dim.scale
            })
            for dim in dims
        }

        data = xr.Dataset(coords=coords)

        super().__init__(name, data, *args, **kwargs)
        self.metadata = metadata or {}
        self.dims = dims
