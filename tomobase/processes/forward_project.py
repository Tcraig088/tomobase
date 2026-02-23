import astra
import numpy as np

from ..utils import _create_projector
from ..data import Volume, Sinogram
from ..log import logger
from ..hooks import process_hook
from ..registers.categories import categories

from magicgui import magicgui
from magicgui.tqdm import trange


@process_hook(name='Project', category=categories['Project'], use_numpy=True)
def project(volume:Volume, angles:np.ndarray, use_gpu:bool=True):
    """Create a sinogram from a volume using forward projection. The GPU Context is overriden due to underlying astra gpu usage. 
    Args:
        volume (Volume): The input volume to be projected.
        angles (np.array): The angles at which to project the volume.
        use_gpu (bool): Whether to use GPU for projection. Default is True.
    Returns:
        Sinogram: The resulting sinogram.

    """
    data = np.transpose(volume.data, (2, 1, 0))  # ASTRA expects (z, y, x)
    angles = np.asarray(angles)
    use_gpu = use_gpu and astra.use_cuda()

    z, y, x = data.shape
    proj_id = _create_projector(x, y, angles, use_gpu)

    sino = np.empty((z, len(angles), max(x, y)))
    for i in trange(z, label="Forward projecting"):
        sino_id, sino[i, :, :] = astra.creators.create_sino(data[i, :, :], proj_id)
        astra.astra.delete(sino_id)

    sinogram = Sinogram(np.transpose(sino, (1,0,2)), angles, volume.pixelsize)  # ASTRA gives (z, n, d)
    astra.astra.delete(proj_id)
    return sinogram