from copy import deepcopy
from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.registrations.environment import xp
from tomobase.data import Sinogram
from typing import Union, Tuple
from tomobase.registrations.progress import progresshandler


_subcategories = ['Misalignment']
@tomobase_hook_process(category=TOMOBASE_TRANSFORM_CATEGORIES.IMAGE_PROCESSING.value, subcategories=_subcategories)
def gaussian_filter(sino: Sinogram, gaussian_sigma:float=1,):
    """Add Gaussian noise to the sinogram.
    Arguments:
        sino (Sinogram): The projection data
        gaussian_sigma (float): Standard deviation of the Gaussian noise (default: 1)
        inplace (bool): Whether to do the operation in-place in the input data object (Default: True)
    Returns:
        sino (sinogram): The result
    """
    sino.data = xp.scipy.ndimage.gaussian_filter(sino.data, gaussian_sigma)
    return sino

@tomobase_hook_process(category=TOMOBASE_TRANSFORM_CATEGORIES.IMAGE_PROCESSING.value, subcategories=_subcategories)
def poisson_noise(sino: Sinogram, 
                  rescale:float=True):
    """Add Poisson noise to the sinogram.
    Arguments:
        sino (Sinogram): The projection data
        rescale (float): Rescale the data to the range of the Poisson noise (default: True)
        inplace (bool): Whether to do the operation in-place in the input data object (Default: True)
    Returns:
        sino (sinogram): The result
    """
    sino.data = sino.data*rescale
    sino.data = xp.random.poisson(sino.data)
    return sino



@tomobase_hook_process(category=TOMOBASE_TRANSFORM_CATEGORIES.IMAGE_PROCESSING.value, subcategories=_subcategories)
def translational_misalignment(sino: Sinogram, offset:float=0.25):
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

    progressbar = progresshandler.add_signal('translational_misalignment')
    progressbar.start(sino.data.shape[0], 'Translational Misalignment')

    
    shifts = xp.xupy.zeros((sino.data.shape[0], 2))
    for i in range(sino.data.shape[0]):
        if i == 0:
            shifts[i, :] = 0
            continue
        image_offset_x = int(xp.xupy.round(sino.data.shape[1] * xp.xupy.random.uniform(-offset, offset)))
        image_offset_y = int(xp.xupy.round(sino.data.shape[2] * xp.xupy.random.uniform(-offset, offset)))
        sino.data[i, :, :] = xp.xupy.roll(sino.data[i, :, :], (image_offset_x, image_offset_y), axis=(0, 1))
        shifts[i, :] = (image_offset_x, image_offset_y)
        progressbar.update(i)
    
    progresshandler.remove_signal('translational_misalignment')

    return sino, shifts

    
    
@tomobase_hook_process(category=TOMOBASE_TRANSFORM_CATEGORIES.IMAGE_PROCESSING.value, subcategories=_subcategories)
def rotational_misalignment(sino: Sinogram, 
                            tilt_theta:float = 3,
                            tilt_alpha:float=2, 
                            backlash:float=0.5, 
                            backlash_backwards:bool =  True):
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
    progressbar = progresshandler.add_signal('rotational_misalignment')
    progressbar.value.start(sino.data.shape[0], 'Rotational Misalignment')

    angles_original =  deepcopy(sino.angles)  
    rotations = xp.xupy.zeros(sino.data.shape[0])
    for i in range(sino.data.shape[0]):
        rotations[i] = tilt_theta * xp.xupy.random.uniform(-1, 1)
        sino.data[i, :, : ] = xp.scipy.ndimage.rotate(sino.data[i, :, :], rotations[i], reshape=False)
        progressbar.update(i)

    for i in range(sino.data.shape[0]):
        offset = tilt_alpha * xp.xupy.random.uniform(-1, 1)
        if i > 0:
            if backlash_backwards and sino.angles[i] < sino.angles[i-1]:
                offset += backlash
            elif not backlash_backwards and sino.angles[i] > sino.angles[i-1]:
                offset += backlash
        sino.angles = sino.angles + offset

    progresshandler.remove_signal(progressbar) 
    return sino, rotations, angles_original

    

    