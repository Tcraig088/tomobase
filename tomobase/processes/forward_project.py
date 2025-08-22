import astra
import numpy as np

from tomobase.utils import _create_projector
from tomobase.data import Volume, Sinogram
from tomobase.log import logger
from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES

from magicgui import magicgui
from magicgui.tqdm import trange


@tomobase_hook_process(name='Project', category=TOMOBASE_TRANSFORM_CATEGORIES.PROJECT.value, use_numpy=True)
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