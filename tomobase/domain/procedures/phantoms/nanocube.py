
from ....core.utils import get_xp
from ....core.data_classes.images import Volume
from ....core import registers

@registers.procedures.register(name="Nanocube", category=registers.categories["Phantoms"])
def get_nanocube(size:int=256,dim:int=512):
    """
    Creates a nanocube phantom.

    Args:
        size (int, optional): The size of the cube. Defaults to 256.
        dim (int, optional): The dimension of the volume. Defaults to 512.

    Returns:
        Volume: The created nanocube phantom.
    """
    xp = get_xp()
    obj = xp.zeros((dim,dim,dim),dtype=xp.float32)
    
    start = int(dim//2-size//2)
    end = int(dim//2+size//2)
    obj[start:end,start:end,start:end] = 1
    return Volume('Nanocube', obj)


