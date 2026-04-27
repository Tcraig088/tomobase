from copy import deepcopy

import scipy


from ....core.data_classes.images import Sinogram
from ....core.base_classes import ImageAbstract
from ....core import registers, progress, logger




subcategory = registers.categories.add_hierarchy('Misalignments', value=5, parent = 'Image Processing')
@registers.procedures.register(category=subcategory)
def gaussian_filter(obj: ImageAbstract, gaussian_sigma:float=1,):
    """Add Gaussian noise to the sinogram.
    Args:
        obj (Data): The input data object
        gaussian_sigma (float): Standard deviation of the Gaussian noise (default: 1)
        inplace (bool): Whether to do the operation in-place in the input data object (Default: True)
    Returns:
        Data: The result
    """
    progress_bar = progress.new(name="Applying Gaussian filter", total=obj.data.sizes['n'])
    for i in progress_bar:
        filtered = scipy.ndimage.gaussian_filter(
            obj.data.isel(n=i).values,
            gaussian_sigma
        )

        obj.data.loc[{ "n": obj.data.coords["n"].values[i] }] = filtered
    return obj

@registers.procedures.register(category=subcategory)
def poisson_noise(obj: ImageAbstract, 
                  rescale:float=1.0):
    """Add Poisson noise to the sinogram.
    Args:
        obj (Data): The input data object
        rescale (float): Rescale the data to the range of the Poisson noise (default: 1.0)
 
    Returns:
        Data: The result
    """
    if (obj.data < 0).any():
        raise ValueError("Poisson noise requires non-negative input data.")

    if rescale <= 0:
        raise ValueError("Rescale factor must be positive.")
    
    xp = obj.data.values.__array_namespace__()
    obj.data = obj.data*rescale
    obj.data.values = xp.random.poisson(obj.data)
    return obj



@registers.procedures.register(category=subcategory)
def translational_misalignment(sino: Sinogram, offset:float=0.25):
    """ Apply a random translational misalignment to the sinogram.
    Arguments:
        sino (Sinogram): The projection data
        offset (float): The maximum offset in pixels (default: 0.25)

    Returns:
        sino (Sinogram): The result
        shifts (ndarray): The shifts applied to each projection (only if extend_return is True)
    """
    xp = sino.data.values.__array_namespace__()
    shifts = xp.zeros((sino.data.sizes['n'], 2))
    
    progress_bar = progress.new(name="Applying translational misalignment", total=sino.data.sizes['n'])
    for i in progress_bar:
        if i == 0:
            shifts[i, :] = 0
            continue
        image_offset_x = int(xp.round(sino.data.sizes['x'] * xp.random.uniform(-offset, offset)))
        image_offset_y = int(xp.round(sino.data.sizes['y'] * xp.random.uniform(-offset, offset)))
        
        
        sl = sino.data.isel(n=i)
        rolled = xp.roll(sl.data,(image_offset_x, image_offset_y),axis=(0, 1))
        sino.data.loc[dict(n=sl.coords["n"].item())] = rolled
        shifts[i, :] = (image_offset_x, image_offset_y)

    return sino, shifts

    
@registers.procedures.register(category=subcategory)
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

    xp = sino.data.values.__array_namespace__()
    rotations = xp.zeros(sino.data.sizes['n'])

    progress_bar = progress.new(name="Applying rotational misalignment", total=sino.data.sizes['n'])
    for i in progress_bar:
        rotations[i] = tilt_theta * xp.random.uniform(-1, 1)
        s1 = sino.data.isel(n=i)
        rotated = scipy.ndimage.rotate(s1.values, rotations[i], reshape=False)
        sino.data.loc[dict(n=s1.coords["n"].item())].values = rotated

    progress_bar = progress.new(name="Applying rotational backlash", total=sino.data.sizes['n'])
    for i in progress_bar:
        offset = tilt_alpha * xp.random.uniform(-1, 1)
        if i > 0:
            if backlash_backwards and sino.angles[i] < sino.angles[i-1]:
                offset += backlash
            elif not backlash_backwards and sino.angles[i] > sino.angles[i-1]:
                offset += backlash
        sino.angles[i] = sino.angles[i] + offset
    logger.trace(f"Data type: {sino.data}")

    return sino, rotations

    

    