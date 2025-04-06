import numpy as np
from tomobase.registrations.environment import TOMOBASE_ENVIRONMENT

if TOMOBASE_ENVIRONMENT.cupy:
    import cupy as cp
    from cupyx.scipy import ndimage as scicp


class GPUHandler():
    instance = None

    def __new__(cls): 
        if cls.instance is None:
            cls.instance = super(GPUHandler, cls).__new__(cls)
        return cls.instance
    
    def __init__(self):
        self.usecupy = TOMOBASE_ENVIRONMENT.cupy
        self.device = 0

    def transpose(self, data, *args, **kwargs):
        if self.usecupy:
            return cp.transpose(data)
        else:
            return np.transpose(data)
        

