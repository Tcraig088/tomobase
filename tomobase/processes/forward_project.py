import astra
import numpy as np
from copy import deepcopy
from scipy import ndimage

from tomobase.utils import _create_projector
from tomobase.data import Volume, Sinogram
from tomobase.log import logger

def project(volume, angles, use_gpu=True, verbose=True):
    """Create a sinogram from a volume using forward projection.

    Arguments:
        volume (Volume)
            The volume
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
    angles = np.asarray(angles)
    use_gpu = use_gpu and astra.use_cuda()

    z, y, x = data.shape
    proj_id = _create_projector(x, y, angles, use_gpu)
    iterator = range(z)

    sino = np.empty((z, len(angles), max(x, y)))
    for i in iterator:
        sino_id, sino[i, :, :] = astra.creators.create_sino(data[i, :, :], proj_id)
        astra.astra.delete(sino_id)

    sinogram = Sinogram(np.transpose(sino, (0, 2, 1)), angles, volume.pixelsize)  # ASTRA gives (z, n, d)
    astra.astra.delete(proj_id)
    return sinogram