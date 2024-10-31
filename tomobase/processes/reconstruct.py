import astra
import numpy as np
from copy import deepcopy
from scipy import ndimage

from tomobase.utils import _create_projector, _get_default_iterations, _circle_mask
from tomobase.data import Volume, Sinogram
from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.log import logger


@tomobase_hook_process(name='Reconstruct', category=TOMOBASE_TRANSFORM_CATEGORIES.RECONSTRUCT.value())
def reconstruct(sino:Sinogram, method:str='sirt', iterations:int=0, use_gpu:bool=True):
    """Reconstruct a volume from a given sinogram.

    Arguments:
        sinogram (Sinogram)
            The projection data
        method (str)
            The reconstruction algorithm; supported algorithms are: `'bp'`,
            `'fbp'`, `'sirt'`, `'em'`, `'sart'` and `'cgls'`
        iterations (int)
            The number of iterations when using an iterative reconstructor,
            leaving this at None will select the default number of iterations
            for the given algorithm (default: None)
        use_gpu (bool)
            Use a GPU if it is available (default: True)
        verbose (bool)
            Display a progress bar if applicable (default: True)
        mask (numpy.ndarray)
            Boolean mask that indicates which voxels should be used in the
            reconstruction (default: None)

    Returns:
        Volume
            The reconstructed volume
    """
    data = np.transpose(sino.data, (0, 2, 1))  # ASTRA expects (z, n, d)
    use_gpu = use_gpu and astra.use_cuda()

    method = method.upper()
    if use_gpu:
        method += '_CUDA'

    # EM is not yet supported on the CPU
    if method == 'EM':
        raise NotImplementedError("The EM method is not yet supported on the CPU.")

    if iterations is None:
        iterations = _get_default_iterations(method)

    z, n, d = data.shape
    proj_id = _create_projector(d, d, sino.angles, use_gpu)

    message = f"Reconstruction using the {method} algorithm on the {'GPU' if use_gpu else 'CPU'}..."
    iterator = range(z)

    vol = np.empty((z, d, d))
    default_mask = _circle_mask(d)

    mask = None
    if mask is None:
        mask = np.ones((z, d, d), dtype=bool)
    else:
        mask = np.transpose(mask, (2, 1, 0))  # ASTRA expects (z, y, x)

    for i in iterator:
        vol_id, vol[i, :, :] = astra.creators.create_reconstruction(
            method, proj_id, data[i, :, :], iterations,
            use_minc='yes', minc=0.0,           # min is zero
            use_maxc='yes', maxc=data.max(),    # max voxel can't be larger than max from sino
            use_mask='yes', mask=default_mask & mask[i, :, :],
        )
        astra.astra.delete(vol_id)

    volume = Volume(np.transpose(vol, (2, 1, 0)), sino.pixelsize)  # ASTRA gives (z, y, x)
    astra.astra.delete(proj_id)
    logger.info('type of volume: ' + str(type(volume)))
    return volume