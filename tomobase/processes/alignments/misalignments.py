
from copy import deepcopy
import numpy as np
from skimage.util import random_noise
from scipy.ndimage import gaussian_filter, rotate
from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.registrations.environment import xp
from tomobase.data import Sinogram
  
_subcategories = {}
_subcategories[TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value] = 'Misalignment'
@tomobase_hook_process(name='Gaussian Filter', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def gaussian_filter(sino: Sinogram, 
              gaussian_sigma:float=1,
              inplace:bool=True):
    """Add Gaussian noise to the sinogram.
    Arguments:
        sino (Sinogram): The projection data
        gaussian_sigma (float): Standard deviation of the Gaussian noise (default: 1)
        inplace (bool): Whether to do the operation in-place in the input data object (Default: True)
    Returns:
        sino (sinogram): The result
    """
    #TODO: Add context shifting
    if not inplace:
        sino = deepcopy(sino)

    # Add Gaussian noise
    sino.data = gaussian_filter(sino.data, gaussian_sigma)
    return sino

@tomobase_hook_process(name='Poisson', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def poisson_noise(sino: Sinogram, 
                  rescale:float=True,
                  inplace:bool=True):
    """Add Poisson noise to the sinogram.
    Arguments:
        sino (Sinogram): The projection data
        rescale (float): Rescale the data to the range of the Poisson noise (default: True)
        inplace (bool): Whether to do the operation in-place in the input data object (Default: True)
    Returns:
        sino (sinogram): The result
    """
    
    if not inplace:
        sino = deepcopy(sino)
    sino.set_context()
    
    sino.data = sino.data*rescale
    sino.data = xp.random.poisson(sino.data)
    return sino



@tomobase_hook_process(name='Translational Misalignment', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def translational_misalignment(sino: Sinogram, 
                               offset:float=0.25, 
                               inplace:bool=True, 
                               extend_return:bool=False):
    """ Apply a random translational misalignment to the sinogram.
    Arguments:
        sino (Sinogram): The projection data
        offset (float): The maximum offset in pixels (default: 0.25)
        inplace (bool): Whether to do the operation in-place in the input data object (Default: True)
        extend_return (bool): Whether to return the shifts as well (default: False)
    Returns:
        sino (Sinogram): The result
        shifts (ndarray): The shifts applied to each projection (only if extend_return is True)
    """
    if not inplace:
        sino = deepcopy(sino)
    sino.set_context()
    
    shifts = xp.zeros((sino.data.shape[2], 2))
    for i in range(sino.data.shape[2]):
        if i == 0:
            shifts[i, :] = 0
            continue
        image_offset_x = int(xp.round(sino.data.shape[1] * np.random.uniform(-offset, offset)))
        image_offset_y = int(xp.round(sino.data.shape[2] * np.random.uniform(-offset, offset)))
        sino.data[i, :, :] = xp.roll(sino.data[i, :, :], (image_offset_x, image_offset_y), axis=(1, 2))
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
    """ Apply a random rotational misalignment to the sinogram.
    Arguments:
        sino (Sinogram): The projection data
        tilt_theta (float): The maximum rotation angle in degrees (default: 3)
        tilt_alpha (float): The maximum offset in degrees (default: 2)
        backlash (float): The maximum backlash in degrees (default: 0.5)
        backlash_backwards (bool): Whether to apply the backlash backwards or forwards (default: True)
        inplace (bool): Whether to do the operation in-place in the input data object (Default: True)
        extend_return (bool): Whether to return the rotations as well (default: False)
    Returns:
        sino (Sinogram): The result
        rotations (ndarray): The rotations applied to each projection (only if extend_return is True)
    """
    #TODO: Add context shifting
    if not inplace:
        sino = deepcopy(sino)
    sino.set_context()
        
    if extend_return:
        angles_original =  deepcopy(sino.angles)
        
    rotations = xp.zeros(sino.data.shape[0])
    for i in range(sino.data.shape[0]):
        rotations[i] = tilt_theta * xp.random.uniform(-1, 1)
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
    

    