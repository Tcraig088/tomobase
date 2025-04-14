
import numpy as np
from copy import copy


from scipy.ndimage import center_of_mass, shift, rotate
from scipy.optimize import minimize_scalar


from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.registrations.environment import xp
from tomobase.registrations.progress import progresshandler

from tomobase.data import Sinogram
from tomobase.processes.reconstruct import astra_reconstruct
from tomobase.processes.forward_project import project
from tomobase.log import logger

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

_subcategories= ['Tilt Axis']
@tomobase_hook_process(name='Tilt Shift', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories, use_numpy=True)
def align_tilt_axis_shift(sino: Sinogram, method:str='fbp', offsets:float=0.0, **kwargs):
    """Align the tilt axis shift of a sinogram using reprojection
    Arguments:
        sino (Sinogram): The projection data
        method (str): The reconstruction algorithm (default: 'fbp')
        offsets (np.ndarray): A list of offsets to try in pixels, if None is given it will use ``numpy.arange(-10, 11)`` (default: None)
        offset (float): A pre-calculated offset in pixels, this is useful for aligning multiple sinograms simultaneously (default: None)
        inplace (bool): Whether to do the alignment in-place in the input data object (default: True)
        extend_return (bool): If True, the return value will be a tuple with the offset in the second item (default: False)
        kwargs (dict): Other keyword arguments are passed to ``reconstruct`` see astra reconstruct
    Returns:
        Sinogram: The result
        offset (float): The offset in pixels
    """
    offset = None
    if offsets == 0.0:
        offsets = np.arange(-10, 11)
    mse = np.zeros(len(offsets))
    sino_shifted = copy(sino)

    progressbar = progresshandler.add_signal('align_tilt_axis_shift')
    progressbar.value.start(len(offsets), 'Aligning tilt axis shift')
    for i in range(len(offsets)):
        sino_shifted.data = shift(sino.data, (0, offsets[i], 0))
        progresshandler.add_subsignal('align_tilt_axis_shift', 'astra_reconstuct')
        reproj = project(astra_reconstruct(sino_shifted, method, **kwargs), sino.angles)
        mse[i] = np.mean((sino_shifted.data - reproj.data) ** 2)
        progressbar.value.update(i)
    offset = offsets[np.argmin(mse)]
    progressbar.value.finish()

    sino.data = shift(sino.data, (0, offset, 0))

    return sino, offset


@tomobase_hook_process(name='Tilt Rotation', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value, subcategories=_subcategories, use_numpy=True)
def align_tilt_axis_rotation(sino:Sinogram, method:str='fbp', angle:float=0.0, **kwargs):
    """Align the tilt axis rotation of a sinogram using reprojection
    Arguments:
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
    
    #TODO: Add context shifting
    angles=None


    if angle == 0.0:
        if angles is None:
            angles = np.arange(-4, 5)
        mse = np.zeros(len(angles))
        sino_rot = copy(sino)

        progressbar = progresshandler.add_signal('align_tilt_axis_rotation')
        progressbar.value.start(len(angles), 'Aligning tilt axis rotation')
        for i in range(len(angles)):
            sino_rot.data = rotate(sino.data, angles[i], reshape=False)
            reproj = project(astra_reconstruct(sino_rot, method, **kwargs),
                            sino.angles)
            mse[i] = np.mean((sino_rot.data - reproj.data) ** 2)
            progressbar.value.update(i)
        angle = angles[np.argmin(mse)]
        progressbar.value.finish()

    sino.data = rotate(sino.data, angle, reshape=False)

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
    
    progressbar = progresshandler.add_signal('backlash_correct')
    progressbar.value.start(sino.data.shape[0], 'Backlash Correction')
    progress = 0

    def objective_function(value, sino, indices):
        angles = copy(sino.angles)
        sino.angles[indices] += value
        reproj = project(astra_reconstruct(sino, 'fbp'), sino.angles[indices])        
        error = np.sqrt(np.mean((sino.data[indices,:,: ] - reproj.data) ** 2))
        sino.angles = angles
        logger.debug(f'Error: {error}')
        progressbar.value.update(progress)
        progress += 1

        if tomobase_logger.progress_bar.max_value < progress:
            tomobase_logger.progress_bar.update_max(progress+10)

        return  error
    
    indices = np.where(np.diff(sino.angles) < 0)[0] + 1
    value = 0

    if method == 'bounded':
        result = minimize_scalar(objective_function, value, args=(sino, indices), bounds=(-tolerance, +tolerance), method=method)
    else:
        result = minimize_scalar(objective_function, value, args=(sino, indices), method=method)
        
    sino.angles[indices] += result.x
    tomobase_logger.progress_bar.finish()
    logger.debug(f'Final Error: {result.fun}, Angle Shift: {result.x}')
    return sino, result.x
