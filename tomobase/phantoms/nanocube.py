import numpy as np

from ..data import Volume
from ..hooks import phantom_hook

@phantom_hook()
def get_nanocube(size:int=256,dim:int=512):
    """
    Creates a nanocube phantom.

    Args:
        size (int, optional): The size of the cube. Defaults to 256.
        dim (int, optional): The dimension of the volume. Defaults to 512.

    Returns:
        Volume: The created nanocube phantom.
    """
    obj = np.zeros((dim,dim,dim),dtype=np.float32)
    start = int(dim//2-size//2)
    end = int(dim//2+size//2)
    obj[start:end,start:end,start:end] = 1
    return Volume(obj)


