
import numpy as np
import copy

import scipy
import cupyx.scipy as cpscipy

from ....core.data_classes.images import Sinogram
from ..reconstruct import project, reconstruct_mlem


from ....core import registers, logger, progress, utils, GPUContext, get_xp

subcategory = registers.categories.add_hierarchy('Tilt Axis Corrections', value=5, parent = 'Align')
@registers.procedures.register(name='Tilt Shift', category=subcategory)
def align_tilt_axis_shift(sino: Sinogram, **kwargs):
    """Align the tilt axis shift of a sinogram using reprojection

    Args:
        sino (Sinogram): The projection data
        method (str): The reconstruction algorithm (default: 'fbp')
        offset (float): A pre-calculated offset in pixels, this is useful for aligning multiple sinograms simultaneously (default: None)
        inplace (bool): Whether to do the alignment in-place in the input data object (default: True)
        extend_return (bool): If True, the return value will be a tuple with the offset in the second item (default: False)
        kwargs (dict): Other keyword arguments are passed to ``reconstruct`` see astra reconstruct
    
    Returns:
        Sinogram: The result
        offset (float): The offset in pixels
    """

    xp = get_xp(sino.data)
    offsets = xp.arange(-10, 11)
    mse = xp.zeros(len(offsets))
    
    try:
        sino_shifted = sino.split('signals')[0]
        s1 = sino.split('signals')[0]
    except:
        sino_shifted = copy.deepcopy(sino)
        s1 = sino
        
    use_3d = kwargs.get('use_3D', True)
    kernel = kwargs.get('kernel', 'astra')
    kwargs['restore_context'] = False
     
    progress_bar = progress.new(name="Calculating tilt axis shift", total=len(offsets))
    for i in progress_bar:
        sino_shifted.data = xp.roll(s1.data, offsets[i], axis=1)
        reproj = project(reconstruct_mlem(sino_shifted, **kwargs), sino_shifted.angles, kernel=kernel, use_3D=use_3d, restore_context=False)
        mse[i] = xp.mean((sino_shifted.data - reproj.data) ** 2)
    offset = offsets[xp.argmin(mse)]


    if "signals" in sino.xr.dims:
        progress_bar = progress.new(name="Applying tilt axis shift", total=sino.xr.sizes['signals'])
        for i in progress_bar:
            s1 = sino.xr.isel(signals=i)
            shifted = xp.roll(s1.data, offset, axis=1)
            sino.xr.loc[dict(signals=s1.coords["signals"].item())] = shifted
    else:
        sino.data = xp.roll(sino.data, offset, axis=1)

    return sino, offset


@registers.procedures.register(name='Tilt Rotation', category=subcategory)
def align_tilt_axis_rotation(sino:Sinogram, angle:float=0.0, **kwargs):
    """Align the tilt axis rotation of a sinogram using reprojection
    Args:
        sino (Sinogram): The projection data
        method (str): The reconstruction algorithm (default: 'fbp')
        angle (float): A pre-calculated angle in degrees, this is useful for aligning multiple sinograms simultaneously (default: None)
        angles (np.ndarray): A list of angles to try in degrees, if None is given it will use ``numpy.arange(-4, 5)`` (default: None)
        inplace (bool): Whether to do the alignment in-place in the input data object (default: True)
        extend_return (bool): If True, the return value will be a tuple with the angle in the second item (default: False)
        kwargs (dict): Other keyword arguments are passed to ``reconstruct`` see astra reconstruct
    
    Returns:
        Sinogram: The result
        angle (float): The angle in degrees
    """
    xp = get_xp(sino.data)
    ndimage = utils.get_module('ndimage', sino.context)
    
    angles = xp.arange(-5+angle, 5+angle)
    mse = xp.zeros(len(angles))
    
    try:
        sino_rot = sino.split('signals')[0]
        s1 = sino.split('signals')[0]
    except:
        sino_rot = copy.deepcopy(sino)
        s1 = sino
    
    use_3d = kwargs.get('use_3D', True)
    kernel = kwargs.get('kernel', 'astra')
    kwargs['restore_context'] = False
     
    progress_bar = progress.new(name="Aligning tilt axis rotation", total=len(angles))
    for i in progress_bar:
        sino_rot.xr.data = ndimage.rotate(s1.data, angles[i], reshape=False, axes=(1,2))
        reproj = project(reconstruct_mlem(sino_rot, **kwargs), sino.angles, use_3D=use_3d, restore_context=False)
        mse[i] = xp.mean((sino_rot.data - reproj.data) ** 2)
            
    angle = angles[xp.argmin(mse)]
    
    if "signals" in sino.xr.dims:
        progress_bar = progress.new(name="Applying tilt axis rotation", total=sino.xr.sizes['signals'])
        for i in progress_bar:
            s1 = sino.xr.isel(signals=i)
            rotated = ndimage.rotate(s1.data, angle, reshape=False, axes=(1,2))
            sino.xr.loc[dict(signals=s1.coords["signals"].item())] = rotated
    else:
        sino.xr.data = ndimage.rotate(sino.xr.data, angle, reshape=False, axes=(1,2))

    return sino, angle

#This backlash correction is experimental and not fully tested
#@tomobase_hook_process(category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories)
def backlash_correct(sino: Sinogram, tolerance:float= 10.0, method:str='bounded'):
    """Correct the backlash of a sinogram using reprojection -  Note this method is currently experimental
    Arguments:
        sino (Sinogram): The projection data
        tolerance (float): The maximum tolerance in degrees (default: 10.0)
        method (str): The optimization method to use (default: 'bounded')
        inplace (bool): Whether to do the alignment in-place in the input data object (default: True)
        extend_return (bool): If True, the return value will be a tuple with the angle in the second item (default: False)
    Returns:
        Sinogram: The result
        angle (float): The angle in degrees
    """
    
    progress = 0
    #TODO Implement 
    def objective_function(value, sino, indices):
        angles = copy(sino.angles)
        sino.angles[indices] += value
        reproj = project(astra_reconstruct(sino, 'fbp'), sino.angles[indices])        
        error = np.sqrt(np.mean((sino.data[indices,:,: ] - reproj.xr) ** 2))
        sino.angles = angles
        logger.debug(f'Error: {error}')
        progress += 1


        return  error
    
    indices = np.where(np.diff(sino.angles) < 0)[0] + 1
    value = 0

    if method == 'bounded':
        result = minimize_scalar(objective_function, value, args=(sino, indices), bounds=(-tolerance, +tolerance), method=method)
    else:
        result = minimize_scalar(objective_function, value, args=(sino, indices), method=method)
        
    sino.angles[indices] += result.x
    logger.debug(f'Final Error: {result.fun}, Angle Shift: {result.x}')
    return sino, result.x
