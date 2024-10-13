
import numpy as np
import copy
import napari

from scipy.ndimage import center_of_mass, shift, rotate

from tomobase.hooks import tomobase_hook_process
from tomobase.enums import TransformCategories

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt

@tomobase_hook_process(name='Align Sinogram XCorrelation', category=TransformCategories.ALIGN)
def align_sinogram_xcorr(sino, inplace=True, verbose=True, shifts=None, return_shifts=False):
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

    if return_shifts:
        return sino, shifts
    else:
        return sino


@tomobase_hook_process(name='Centre of Mass', category=TransformCategories.ALIGN)
def align_sinogram_center_of_mass(sino, inplace=True, offset=None, return_offset=False):
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

    if offset is None:
        offset = np.asarray(sino.data.shape[:2]) / 2 - center_of_mass(np.sum(sino.data, axis=2))

    sino.data = shift(sino.data, (offset[0], offset[1], 0))

    if return_offset:
        return sino, offset
    else:
        return sino