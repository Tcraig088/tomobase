import numpy as np
import copy
import napari


from scipy.ndimage import center_of_mass, circshift, rotate
from tomobase.hooks import tomobase_hook_process
from tomobase.enums import TransformCategories

from qtpy.QtWidgets import QWidget, QComboBox, QLabel, QSpinBox, QHBoxLayout, QLineEdit, QVBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox
from qtpy.QtCore import Qt


@tomobase_hook_process(name='Add Noise', category=TransformCategories.ALIGN)
def add_noise(sino, gaussian_mean=0, gaussian_sigma=1, poisson_noise= 0.5, inplace=True):
    """Add Gaussian and Poisson noise to the sinogram.

    Arguments:
        sino (Sinogram)
            The projection data
        gaussian_mean (float)
            Mean of the Gaussian noise (default: 0)
        gaussian_sigma (float)
            Standard deviation of the Gaussian noise (default: 1)
        poisson_noise (bool)
            Whether to add Poisson noise (default: True)
        inplace (bool)
            Whether to do the operation in-place in the input data object
            (default: True)

    Returns:
        Sinogram
            The result
    """
    if not inplace:
        sino = copy.deepcopy(sino)

    # Add Gaussian noise
    gaussian_noise = np.random.normal(gaussian_mean, gaussian_sigma, sino.data.shape)
    sino.data += gaussian_noise

    # Add Poisson noise
    if poisson_noise>0:
        min_val = np.min(sino.data)
        if min_val < 0:
            sino.data -= min_val
            sino.data = np.random.poisson(sino.data)
            sino.data += min_val
        else:
            sino.data = np.random.poisson(sino.data)

    return sino

@tomobase_hook_process(name='Random Translation', category=TransformCategories.ALIGN)
def random_translation(sino, offset=0.25, inplace=True, return_offset=False):
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

    for i in range(sino.data.shape[2]):
        image_offset_x = np.round(sino.data.shape[0] * np.random.uniform(-offset, offset))
        image_offset_y = np.round(sino.data.shape[1] * np.random.uniform(-offset, offset))
        sino.data[:, :, i] = np.roll(sino.data[:, :, i], (image_offset_x, image_offset_y), order=3)

    if return_offset:
        return sino, offset
    else:
        return sino