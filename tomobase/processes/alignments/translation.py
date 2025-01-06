
import numpy as np
from copy import copy
import napari

from scipy.ndimage import center_of_mass, shift, rotate

from tomobase.hooks import tomobase_hook_process
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
from tomobase.data import Sinogram

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

_subcategories = {}
_subcategories[TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value()] = 'Translation'
@tomobase_hook_process(name='Pad Sinogram', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories = _subcategories)
def pad_sinogram(sino:Sinogram, x:int=0, y:int=0, inplace: bool =True):
    """_summary_

    Args:
        sino (_type_): _description_
        x (int, optional): _description_. Defaults to 0.
        y (int, optional): _description_. Defaults to 0.
        inplace (bool, optional): _description_. Defaults to True.

    Raises:
        ValueError: _description_

    Returns:
        _type_: _description_
    """
    if not inplace:
        sino = copy(sino)

    pad_x = x - sino.data.shape[0]
    pad_y = y - sino.data.shape[1]
    if pad_x < 0 or pad_y < 0:
        raise ValueError("Cannot pad to a smaller size")
    sino.data = np.pad(sino.data, ((pad_x//2, pad_x//2), (pad_y//2, pad_y//2), (0, 0)), mode='constant')

    return sino




@tomobase_hook_process(name='Align Sinogram XCorrelation', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories = _subcategories)
def align_sinogram_xcorr(sino:Sinogram, inplace: bool =True, shifts= None, extend_return:bool=False):
    """Align all projection images to each other using cross-correlation

    This method can only align projection images to each other with an accuracy
    of 1 pixel. Use another method if subpixel accuracy is required.

    Arguments:
        sino (Sinogram)
            The projection data
        inplace (bool)
            Whether to do the alignment in-place in the input data object
            (default: True)
        verbose (bool)
            Display a progress bar if applicable (default: True)
        shifts (numpy.ndarray)
            Nx2 array containing the shifts to align the images to each other.
            If this argument is set, no cross-correlation will be calculated but
            the shifts will directly be applied. This is useful for aligning a
            sinogram containing data from a different modality (e.g. for EDX
            tomography). (default: None)
        return_shifts (bool)
            If True, the return value will be a tuple with the shifts for each
            projection image in the second item (default: False)

    Returns:
        Sinogram
            The result
    """
    if not inplace:
        sino = copy(sino)

    if shifts is None:
        shifts = np.zeros((sino.data.shape[2], 2))
        fft_fixed = np.fft.fft2(sino.data[:, :, 0])
        for i in range(sino.data.shape[2] - 1):
            fft_moving = np.fft.fft2(sino.data[:, :, i+1])
            xcorr = np.fft.ifft2(np.multiply(fft_fixed, np.conj(fft_moving)))
            fft_fixed = fft_moving
            rel_shift = np.asarray(np.unravel_index(np.argmax(xcorr), xcorr.shape))
            shifts[i+1, :] = shifts[i, :] + rel_shift

        shifts %= np.asarray(sino.data.shape[:2])[None, :]
        shifts = np.rint(shifts).astype(int)

    for i in range(sino.data.shape[2]):
        sino.data[:, :, i] = np.roll(sino.data[:, :, i], shifts[i, :], axis=(0, 1))

    if extend_return:
        return sino, shifts
    else:
        return sino


@tomobase_hook_process(name='Centre of Mass', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories = _subcategories)
def align_sinogram_center_of_mass(sino:Sinogram, inplace:bool=True, extend_return:bool=False):
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
        sino = copy(sino)


    offset = np.asarray(sino.data.shape[:2]) / 2 - center_of_mass(np.sum(sino.data, axis=2))

    sino.data = shift(sino.data, (offset[0], offset[1], 0))

    if extend_return:
        return sino, offset
    else:
        return sino
    
@tomobase_hook_process(name='Weight by Angle', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories = _subcategories)
def weight_by_angle(sino:Sinogram, inplace:bool=True, extend_return:bool=False):
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
        sino = copy(sino)

    indices = np.argsort(sino.angles)
    sino.angles = sino.angles[indices]
    sino.data = sino.data[:,:,indices]
    weights= np.ones_like(sino.angles)

    sorted_angles = copy(sino.angles) +  90
    n_angles = len(sorted_angles)
    print(n_angles)
    for i in range(len(sorted_angles)):
        if i == 0:
            weights[i] = 0.5*(180 - sorted_angles[n_angles-1] + sorted_angles[i+1])
        elif i == len(sorted_angles)-1:
            weights[i] = 0.5*(180 - sorted_angles[n_angles-2] + sorted_angles[0])
        else:
            weights[i] = 0.5*((sorted_angles[i+1] - sorted_angles[i]) + (sorted_angles[i] - sorted_angles[i-1]))
    ratio = 180/(n_angles-1)
    weights = weights/ratio

    sino.data = sino.data * weights

    if extend_return:
        return sino, weights
    else:
        return sino
