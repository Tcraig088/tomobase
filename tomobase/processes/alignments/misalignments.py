import numpy as np
from copy import deepcopy

from skimage.util import random_noise
from scipy.ndimage import gaussian_filter, rotate
from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.data import Sinogram
  
_subcategories = {}
_subcategories[TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value] = 'Misalignment'
@tomobase_hook_process(name='Gaussian Filter', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def gaussian_filter(sino: Sinogram, 
              gaussian_sigma:float=1,
              inplace:bool=True):
    """_summary_

    Args:
        sino (Sinogram): _description_
        gaussian_sigma (float, optional): _description_. Defaults to 1.
        inplace (bool, optional): _description_. Defaults to True.

    Returns:
        _type_: _description_
    """
    if not inplace:
        sino = deepcopy(sino)

    # Add Gaussian noise
    sino.data = gaussian_filter(sino.data, gaussian_sigma)
    return sino

@tomobase_hook_process(name='Poisson', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def poisson_noise(sino: Sinogram, 
                  rescale:float=True,
                  inplace:bool=True):
    """Add Gaussian and Poisson noise to the sinogram.

    Arguments:
        sino (Sinogram)
            The projection data
        gaussian_mean (float)
            Mean of the Gaussian noise (default: 0)
        gaussian_sigma (float)
            Standard deviation of the Gaussian noise (default: 1)
        poisson_noise (bool)
            Whether to add Poisson noise (default: True)
        inplace (bool)
            Whether to do the operation in-place in the input data object
            (default: True)

    Returns:
        Sinogram
            The result
    """
    if not inplace:
        sino = deepcopy(sino)

    sino.data = sino.data*rescale
    sino.data = np.random.poisson(sino.data)
    return sino



@tomobase_hook_process(name='Translational Misalignment', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def translational_misalignment(sino: Sinogram, 
                               offset:float=0.25, 
                               inplace:bool=True, 
                               extend_return:bool=False):
    """Align the projection images to their collective center of mass

    This function uses 3rd order spline interpolation to achieve sub-pixel
    precision.

    Arguments:
        sino (Sinogram)
            The projection data
        inplace (bool)
            Whether to do the alignment in-place in the input data object
            (default: True)
        offset (numpy.ndarray)
            A pre-calculated offset for aligning multiple sinograms
            simultaneously (e.g. useful for EDX tomography) (default: None)
        return_offset (bool)
            If True, the return value will be a tuple with the offset in the
            second item (default: False)

    Returns:
        Sinogram
            The result
    """
    if not inplace:
        sino = deepcopy(sino)

    shifts = np.zeros((sino.data.shape[2], 2))
    for i in range(sino.data.shape[2]):
        if i == 0:
            shifts[i, :] = 0
            continue
        image_offset_x = int(np.round(sino.data.shape[1] * np.random.uniform(-offset, offset)))
        image_offset_y = int(np.round(sino.data.shape[2] * np.random.uniform(-offset, offset)))
        sino.data[i, :, :] = np.roll(sino.data[i, :, :], (image_offset_x, image_offset_y), axis=(1, 2))
        shifts[i, :] = (image_offset_x, image_offset_y)
    if extend_return:
        return sino, shifts
    else:
        return sino
    
    
@tomobase_hook_process(name='Rotational Misalignment', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def rotational_misalignment(sino: Sinogram, 
                            tilt_theta:float = 3,
                            tilt_alpha:float=2, 
                            backlash:float=0.5, 
                            backlash_backwards:bool =  True, 
                            inplace:bool=True, 
                            extend_return:bool=False):
    """ Rotate the projection images to simulate drift in the tilt axis
    if not inplace:
        sino = copy(sino)
    """
    if not inplace:
        sino = deepcopy(sino)
        
    if extend_return:
        angles_original =  deepcopy(sino.angles)
        
    rotations = np.zeros(sino.data.shape[0])
    for i in range(sino.data.shape[0]):
        rotations[i] = tilt_theta * np.random.uniform(-1, 1)
        sino.data[i, :, : ] = rotate(sino.data[i, :, :], rotations[i], reshape=False)
    

    for i in range(sino.data.shape[0]):
        offset = tilt_alpha * np.random.uniform(-1, 1)
        if i > 0:
            if backlash_backwards and sino.angles[i] < sino.angles[i-1]:
                offset += backlash
            elif not backlash_backwards and sino.angles[i] > sino.angles[i-1]:
                offset += backlash
        sino.angles = sino.angles + offset  
             
    if extend_return:
        return sino, rotations, angles_original
    else:
        return sino
    

    