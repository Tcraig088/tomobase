import numpy as np
from tomobase.data import Volume
from tomobase.hooks import phantom_hook

@phantom_hook()
def nanocube(size=256,dim=512):
    obj = np.zeros((dim,dim,dim),dtype=np.float32)
    start = int(dim//2-size//2)
    end = int(dim//2+size//2)
    obj[start:end,start:end,start:end] = 1
    return Volume(obj)


