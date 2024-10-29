
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
_subcategories[TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value()] = 'Tilt Axis'
@tomobase_hook_process(name='Align Tilt Shift', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories=_subcategories)
def align_tilt_axis_shift(sino: Sinogram, method='sirt', offsets=None, offset=None,
                          inplace=True, verbose=True, return_offset=False, **kwargs):
    """Align the horizontal shift of the tilt axis of a sinogram other using
    reprojection

    To apply this algorithm, the sinogram must already be roughly aligned, with
    ``align_sinogram_center_of_mass`` for example. Multiple iterations of this
    method might be required for optimal alignment.

    Arguments:
        sino (Sinogram)
            The projection data
        method (str)
            The reconstruction algorithm (default: 'sirt')
        offsets (numpy.ndarray)
            A list of horizontal offsets to try, if None is given it will use
            ``numpy.arange(-10, 11)`` (default: None)
        offset (float)
            A pre-calculated tilt axis offset, can be used if the offset is
            known by calculating it for a reference sinogram (default: None)
        inplace (bool)
            Whether to do the alignment in-place in the input data object
            (default: True)
        verbose (bool)
            Display a progress bar if True (default: True)
        return_offset (bool)
            If True, the return value will be a tuple with the offset in the
            second item (default: False)
        kwargs (dict)
            Other keyword arguments are passed to ``reconstruct``

    Returns:
        Sinogram
            The result
    """
    if not inplace:
        sino = copy(sino)

    if offset is None:
        if offsets is None:
            offsets = np.arange(-10, 11)
        mse = np.zeros(len(offsets))
        sino_shifted = copy(sino)
        for i in range(len(offsets)):
            sino_shifted.data = shift(sino.data, (0, offsets[i], 0))
            reproj = project(reconstruct(sino_shifted, method, **kwargs),
                             sino.angles)
            mse[i] = np.mean((sino_shifted.data - reproj.data) ** 2)

        offset = offsets[np.argmin(mse)]

    sino.data = shift(sino.data, (0, offset, 0))

    if return_offset:
        return sino, offset
    else:
        return sino
    
    
@tomobase_hook_process(name='Align Tilt Rotation', category=TOMOBASE_TRANSFORM_CATEGORIES.ALIGN.value(), subcategories=_subcategories)
def align_tilt_axis_rotation(sino: Sinogram, method='sirt', angles=None, angle=None,
                             inplace=True, verbose=True, return_angle=False, **kwargs):
    """Align the rotation of the tilt axis of a sinogram other using
    reprojection

    To apply this algorithm, the sinogram must already be roughly aligned, with
    ``align_sinogram_center_of_mass`` and ``align_tilt_axis_shift`` for example.
    Multiple iterations of this method might be required for optimal alignment.

    Arguments:
        sino (Sinogram)
            The projection data
        method (str)
            The reconstruction algorithm (default: 'sirt')
        angles (np.ndarray)
            A list of angles to try in degrees, if None is given it will use
            ``numpy.arange(-4, 5)`` (default: None)
        angle (float)
            A pre-calculated angle in degrees, this is useful for aligning
            multiple sinograms simultaneously (default: None)
        inplace (bool)
            Whether to do the alignment in-place in the input data object
            (default: True)
        verbose (bool)
            Display a progress bar if applicable (default: True)
        return_angle (bool)
            If True, the return value will be a tuple with the angle in the
            second item (default: False)
        kwargs (dict)
            Other keyword arguments are passed to ``reconstruct``

    Returns:
        Sinogram
            The result
    """
    if not inplace:
        sino = copy(sino)

    if angle is None:
        if angles is None:
            angles = np.arange(-4, 5)
        mse = np.zeros(len(angles))
        sino_rot = copy(sino)
        for i in range(len(angles)):
            sino_rot.data = rotate(sino.data, angles[i], reshape=False)
            reproj = project(reconstruct(sino_rot, method, **kwargs),
                            sino.angles)
            mse[i] = np.mean((sino_rot.data - reproj.data) ** 2)

        angle = angles[np.argmin(mse)]

    sino.data = rotate(sino.data, angle, reshape=False)

    if return_angle:
        return sino, angle
    else:
        return sino
