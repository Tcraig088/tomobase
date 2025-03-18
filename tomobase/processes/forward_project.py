import astra
import numpy as np
from copy import deepcopy
from scipy import ndimage

from tomobase.typehints import TILTANGLETYPE
from tomobase.utils import _create_projector
from tomobase.data import Volume, Sinogram
from tomobase.log import logger
from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES


@tomobase_hook_process(name='Project', category=TOMOBASE_TRANSFORM_CATEGORIES.PROJECT.value())
def project(volume:Volume, angles:TILTANGLETYPE, use_gpu:bool=True):
    """Create a sinogram from a volume using forward projection.

    Arguments:
        volume (Volume)
            The volum e
        angles (iterable)
            The projection angles in degrees
        use_gpu (bool)
            Use a GPU if it is available (default: True)
        verbose (bool)
            Display a progress bar if applicable (default: True)

    Returns:
        Sinogram
            The projection data
    """
    data = np.transpose(volume.data, (2, 1, 0))  # ASTRA expects (z, y, x)
    if isinstance(angles, tuple):
        angles = np.array([angles[0].get_angle() for i in range(angles[1])]) 
    angles = np.asarray(angles)
    use_gpu = use_gpu and astra.use_cuda()

    z, y, x = data.shape
    proj_id = _create_projector(x, y, angles, use_gpu)
    iterator = range(z)

    sino = np.empty((z, len(angles), max(x, y)))
    for i in iterator:
        sino_id, sino[i, :, :] = astra.creators.create_sino(data[i, :, :], proj_id)
        astra.astra.delete(sino_id)

    sinogram = Sinogram(np.transpose(sino, (1,2,0)), angles, volume.pixelsize)  # ASTRA gives (z, n, d)
    astra.astra.delete(proj_id)
    return sinogram