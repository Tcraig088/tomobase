import astra
import numpy as np
from copy import deepcopy
from scipy import ndimage

from tomobase.utils import _create_projector, _get_default_iterations, _circle_mask
from tomobase.data import Volume, Sinogram
from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.registrations.progress import progresshandler
from tomobase.log import  tomobase_logger, logger

@tomobase_hook_process(name='OpTomo', category=TOMOBASE_TRANSFORM_CATEGORIES.RECONSTRUCT.value, use_numpy=True)
def optomo_reconstruct(sino:Sinogram, iterations:int=0, use_gpu:bool=True, weighted:bool=False):
    """Reconstruct a volume from a given sinogram.
    Arguments:
        sino (Sinogram): The projection data
        iterations (int):
            The number of iterations when using an iterative reconstructor,
            leaving this at None will select the default number of iterations
            for the given algorithm (default: None)
        use_gpu (bool): Use a GPU if it is available (default: True)
        weighted (bool): Use a weighted backprojection (default: False)
            
    Returns:    
        Volume: The reconstructed volume
    """
    indices = np.argsort(sino.angles)
    sino.angles = sino.angles[indices]
    data = sino.data[indices, : ,:]
    data = np.transpose(data, (1,0,2)) # ASTRA expects (z, n, d)
 
    weights= np.ones_like(sino.angles)
    if weighted == True:
        sorted_angles = deepcopy(sino.angles) +  90
        n_angles = len(sorted_angles)
        for i in range(len(sorted_angles)):
            if i == 0:
                weights[i] = 0.5*(180 - sorted_angles[n_angles-1] + sorted_angles[i+1])
            elif i == len(sorted_angles)-1:
                weights[i] = 0.5*(180 - sorted_angles[n_angles-2] + sorted_angles[0])
            else:
                weights[i] = 0.5*((sorted_angles[i+1] - sorted_angles[i]) + (sorted_angles[i] - sorted_angles[i-1]))
        ratio = 180/(n_angles-1)
        weights = weights/ratio
    
    
    use_gpu = use_gpu and astra.use_cuda()

    if iterations is None:
        iterations = _get_default_iterations('sirt')

    z, n, d = data.shape
    proj_id = _create_projector(d, d, sino.angles, use_gpu)

    iterator = range(z)

    vol = np.zeros((z, d, d))
    default_mask = _circle_mask(d)

    mask = None
    if mask is None:
        mask = np.ones((z, d, d), dtype=bool)
    else:
        mask = np.transpose(mask, (2, 1, 0))  # ASTRA expects (z, y, x)

    W = astra.OpTomo(proj_id)
    domain_shape = np.ones((d, d))
    range_shape = np.ones((n, d))
    R = np.reshape(1/(W*domain_shape), (n, d))
    C = np.reshape(1/(W.T*range_shape), (d, d))
    R = np.minimum(R, 1 / 10**-6)
    C = np.minimum(C, 1 / 10**-6)

    slice_progressbar = progresshandler.add_signal('optomo_reconstruct')
    slice_progressbar.value.start(z, 'Reconstruction Slices with Optomo')

    for i in iterator:
        for j in range(iterations):
            iteration_progressbar = progresshandler.add_subsignal('optomo_reconstruct')
            iteration_progressbar.start(iterations, 'Reconstruction Iterations with Optomo')
            A = np.transpose(np.transpose(np.reshape(W*vol[i, :, :], (n, d)), (1,0))*weights,(1,0)) 
            B = np.transpose(np.reshape(np.transpose(data[i, :, :],(1,0))*weights,(d,n)), (1,0))
            D = R*(B - A)
            vol[i, :, :] += C*np.reshape(W.T*D,(d,d))
            vol[i, :, :] = np.reshape(np.minimum(vol[i, :, :], data.max()), (d, d))
            vol[i, :, :] = np.reshape(np.maximum(vol[i, :, :], 0), (d, d))
            vol[i, :, :] = vol[i, :, :] * (default_mask & mask[i, :, :])
            iteration_progressbar.value.update(j)
        progresshandler.remove_signal(iteration_progressbar)
        slice_progressbar.value.update(i)
    progresshandler.remove_signal(slice_progressbar)



            


    volume = Volume(np.transpose(vol, (2, 1,0)), sino.pixelsize)  # ASTRA gives (z, y, x)
    astra.astra.delete(proj_id)
    logger.info('type of volume: ' + str(type(volume)))
    return volume


@tomobase_hook_process(name='Astra', category=TOMOBASE_TRANSFORM_CATEGORIES.RECONSTRUCT.value, use_numpy=True)
def astra_reconstruct(sino:Sinogram, method:str='sirt', iterations:int=0, use_gpu:bool=True):
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
    logger.info('Reconstructing...')
    data = np.transpose(sino.data, (1,0,2))  # ASTRA expects (z, n, d)
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
    logger.info(message)
    iterator = range(z)

    vol = np.empty((z, d, d))
    default_mask = _circle_mask(d)

    mask = None
    if mask is None:
        mask = np.ones((z, d, d), dtype=bool)
    else:
        mask = np.transpose(mask, (2, 1, 0))  # ASTRA expects (z, y, x)

    progressbar = progresshandler.add_signal('astra_reconstruct')
    progressbar.value.start(z, 'Reconstruction Iteratively with Astra')
    for i in iterator:
        vol_id, vol[i, :, :] = astra.creators.create_reconstruction(
            method, proj_id, data[i, :, :], iterations,
            use_minc='yes', minc=0.0,           # min is zero
            use_maxc='yes', maxc=data.max(),    # max voxel can't be larger than max from sino
            use_mask='yes', mask=default_mask & mask[i, :, :],
        )
        progressbar.value.update(i)
        astra.astra.delete(vol_id)
        
    progresshandler.remove_signal(progressbar)
    volume = Volume(np.transpose(vol, (2, 1, 0)), sino.pixelsize)  # ASTRA gives (z, y, x)
    astra.astra.delete(proj_id)
    logger.info('type of volume: ' + str(type(volume)))
    return volume

