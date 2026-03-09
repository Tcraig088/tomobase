from copy import deepcopy

from ...hooks import process_hook
from ...registers.categories import categories
from ...environment import proxy
from ...data import Sinogram, Image

from typing import Union, Tuple
from magicgui.tqdm import tqdm


subcategory = categories.add_category('Misalignments', value=5, inheritor = 'Image Processing')
@process_hook(category=subcategory)
def gaussian_filter(obj: Image, gaussian_sigma:float=1,):
    """Add Gaussian noise to the sinogram.
    Args:
        obj (Data): The input data object
        gaussian_sigma (float): Standard deviation of the Gaussian noise (default: 1)
        inplace (bool): Whether to do the operation in-place in the input data object (Default: True)
    Returns:
        Data: The result
    """
    obj.data = proxy.scipy.ndimage.gaussian_filter(obj.data, gaussian_sigma)
    return obj

@process_hook(category=subcategory)
def poisson_noise(obj: Image, 
                  rescale:float=True):
    """Add Poisson noise to the sinogram.
    Args:
        obj (Data): The input data object
        rescale (float): Rescale the data to the range of the Poisson noise (default: True)
 
    Returns:
        Data: The result
    """
    obj.data = obj.data*rescale
    obj.data = proxy.xupy.random.poisson(obj.data)
    return obj



@process_hook(category=subcategory)
def translational_misalignment(sino: Sinogram, offset:float=0.25):
    """ Apply a random translational misalignment to the sinogram.
    Arguments:
        sino (Sinogram): The projection data
        offset (float): The maximum offset in pixels (default: 0.25)

    Returns:
        sino (Sinogram): The result
        shifts (ndarray): The shifts applied to each projection (only if extend_return is True)
    """
    
    shifts = proxy.xupy.zeros((sino.data.shape[0], 2))
    for i in tqdm(range(sino.data.shape[0]), label='Translational Misalignment'):
        if i == 0:
            shifts[i, :] = 0
            continue
        image_offset_x = int(proxy.xupy.round(sino.data.shape[1] * proxy.xupy.random.uniform(-offset, offset)))
        image_offset_y = int(proxy.xupy.round(sino.data.shape[2] * proxy.xupy.random.uniform(-offset, offset)))
        sino.data[i, :, :] = proxy.xupy.roll(sino.data[i, :, :], (image_offset_x, image_offset_y), axis=(0, 1))
        shifts[i, :] = (image_offset_x, image_offset_y)


    return sino, shifts

    
    
@process_hook(category=subcategory)
def rotational_misalignment(sino: Sinogram, 
                            tilt_theta:float = 3,
                            tilt_alpha:float=2, 
                            backlash:float=0.5, 
                            backlash_backwards:bool =  True):
    """ Apply a random rotational misalignment to the sinogram.
    Args:
        sino (Sinogram): The projection data
        tilt_theta (float): The maximum rotation angle in degrees (default: 3)
        tilt_alpha (float): The maximum offset in degrees (default: 2)
        backlash (float): The maximum backlash in degrees (default: 0.5)
        backlash_backwards (bool): Whether to apply the backlash backwards or forwards (default: True)

    Returns:
        sino (Sinogram): The result
        rotations (ndarray): The rotations applied to each projection (only if extend_return is True)
    """

    angles_original =  deepcopy(sino.angles)  
    rotations = proxy.xupy.zeros(sino.data.shape[0])
    for i in tqdm(range(sino.data.shape[0]), label='Rotational Misalignment'):
        rotations[i] = tilt_theta * proxy.xupy.random.uniform(-1, 1)
        sino.data[i, :, : ] = proxy.scipy.ndimage.rotate(sino.data[i, :, :], rotations[i], reshape=False)


    for i in range(sino.data.shape[0]):
        offset = tilt_alpha * proxy.xupy.random.uniform(-1, 1)
        if i > 0:
            if backlash_backwards and sino.angles[i] < sino.angles[i-1]:
                offset += backlash
            elif not backlash_backwards and sino.angles[i] > sino.angles[i-1]:
                offset += backlash
        sino.angles = sino.angles + offset

    return sino, rotations, angles_original

    

    