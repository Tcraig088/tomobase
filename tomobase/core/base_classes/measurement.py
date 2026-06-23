import coolname
import copy

from .components import ContextModel, IOModel, SignalModel
from ...core.environment import get_xp, GPUContext

import xarray as xr


    
class MeasurementAbstract(SignalModel, IOModel):
    """Base class for measurement models. This is to be used as a template for creating measurement models such as Sinogram, Volume etc. also useful for type hinting."""
    
    def __init__(self, name, data, metadata=None, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self.name = name
        
    def __str__(self):
        msg = f"{self.__class__.__name__}:\n"
        msg += f"  Sample Name: {self.name}\n"
        msg += f"  Data Shape: {self.xr.shape} Data Type: {self.xr.dtype}\n"
        return msg