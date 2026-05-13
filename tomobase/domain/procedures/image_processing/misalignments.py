from copy import deepcopy

from ....core.data_classes.images import Sinogram
from ....core.base_classes import ImageAbstract
from ....core import registers, progress, logger, utils, GPUContext, get_xp




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
    xp = get_xp(obj.data)
    ndimage = utils.get_module('ndimage', obj.context)

    total, indexer = utils.iter_indexers_with_len({d: obj.xr.sizes[d] for d in obj.non_spatial_dims}, obj.non_spatial_dims)
    progress_bar = progress.new(name="Applying Gaussian filter", total=total)
    for i in progress_bar:
        idx = next(indexer)
        filtered = ndimage.gaussian_filter(
            obj.xr.isel(idx).values,
            gaussian_sigma
        )

        obj.xr.loc[idx] = filtered
    return obj

@registers.procedures.register(category=subcategory)
def poisson_noise(image: ImageAbstract, 
                  rescale:float=1.0):
    """Add Poisson noise to the sinogram.
    Args:
        image (ImageAbstract): The input data object
        rescale (float): Rescale the data to the range of the Poisson noise (default: 1.0)
 
    Returns:
        ImageAbstract: The result
    """
    if (image.data < 0).any():
        raise ValueError("Poisson noise requires non-negative input data.")

    if rescale <= 0:
        raise ValueError("Rescale factor must be positive.")
    
    xp = get_xp(image.data)
    image.data = image.data*rescale
    image.data = xp.random.poisson(image.data)
    return image



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
    xp = get_xp(sino.data)
    shifts = xp.zeros((sino.xr.sizes['n'], 2))
    
    total, indexer = utils.iter_indexers_with_len({d: sino.xr.sizes[d] for d in sino.non_spatial_dims}, sino.non_spatial_dims)
    progress_bar = progress.new(name="Applying translational misalignment", total=total)
    for i in progress_bar:
        idx = next(indexer)
        if i == 0:
            shifts[i, :] = 0
            continue
        image_offset_x = int(xp.round(sino.xr.sizes['x'] * xp.random.uniform(-offset, offset)))
        image_offset_y = int(xp.round(sino.xr.sizes['y'] * xp.random.uniform(-offset, offset)))
        
        
        sl = sino.xr.isel(idx)
        rolled = xp.roll(sl.data,(image_offset_x, image_offset_y),axis=(0, 1))
        sino.xr.loc[idx] = rolled
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

    xp = get_xp(sino.data)
    ndimage = utils.get_module('ndimage', sino.context)
        
    rotations = xp.zeros(sino.xr.sizes['n'])
    
    if "signals" in sino.xr.dims:
        dims = {"signals": 0, "n": 0}
    else:
        dims = {"n": 0}
        
    progress_bar = progress.new(name="Calculating rotational misalignment", total=sino.xr.sizes['n'])
    for i in progress_bar:
        rotations[i] = tilt_theta * xp.random.uniform(-1, 1)
        
    total, indexer = utils.iter_indexers_with_len({d: sino.xr.sizes[d] for d in sino.non_spatial_dims}, sino.non_spatial_dims)   
    progress_bar = progress.new(name="Applying rotational misalignment", total=total)
    for i in progress_bar:
        idx = next(indexer)
        s1 = sino.xr.isel(dims)
        rotated = ndimage.rotate(s1.data, rotations[idx["n"]], reshape=False)
        sino.xr.loc[dims].data = rotated
        
    progress_bar = progress.new(name="Applying rotational backlash", total=sino.xr.sizes['n'])
    for i in progress_bar:
        offset = tilt_alpha * xp.random.uniform(-1, 1)
        if i > 0:
            if backlash_backwards and sino.angles[i] < sino.angles[i-1]:
                offset += backlash
            elif not backlash_backwards and sino.angles[i] > sino.angles[i-1]:
                offset += backlash
        sino.angles[i] = sino.angles[i] + offset
    logger.trace(f"Data type: {sino.xr}")

    return sino, rotations

    

    