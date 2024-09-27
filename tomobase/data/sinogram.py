import os
import glob
import numpy as np
import imageio as iio
import napari

from qtpy.QtWidgets import QApplication, QFileDialog
import collections
collections.Iterable = collections.abc.Iterable

from abc import ABC, abstractmethod


from tomobase.registration import TOMOBASE_ENVIRONMENT_REGISTRATION
if TOMOBASE_ENVIRONMENT_REGISTRATION.hyperspy:
    import hyperspy.api as hs
    
from tomobase.data.base import Data
from tomobase.registration import TOMOBASE_DATATYPES
from tomobase.data.image import Image

class Sinogram(Data):
    """A stack of projection images

    Attributes:
        data (numpy.ndarray)
            The data as a stack of images. The data is indexed using the
            (rows, columns, slices) standard, which corresponds to (y, x, alpha)
        angles (numpy.ndarray)
            The tilt angles in degrees corresponding to the projection images
        pixelsize (float)
            The width of the pixels in nanometer (default 1.0)
    """

    def __init__(self, data, angles, pixelsize=1.0):
        """Create a sinogram

        Arguments:
            data (numpy.ndarray)
                The data as a stack of images. The data is indexed using the
                (rows, columns, slices) standard, which corresponds to
                (y, x, alpha)
            angles (numpy.ndarray)
                The tilt angles in degrees corresponding to the projection
                images
            pixelsize (float)
                The width of the pixels in nanometer (default 1.0)
        """
        if len(angles) != data.shape[2]:
            raise ValueError(("There should be the same number of projection "
                              "images as tilt angles."))
        super().__init__(data, pixelsize)
        self.angles = np.asarray(angles)


    @staticmethod
    def _read_mrc(filename, **kwargs):
        # TODO make this method independent of Hyperspy
        content = hs.load(filename, lazy=False, reader='mrc')
        data = np.asarray(content.data, dtype=float)
        data = np.transpose(data, (2, 1, 0))  # TODO check orientation
        angles = np.asarray(content.metadata.Acquisition_instrument.TEM.Stage.tilt_alpha)[:data.shape[2]]
        pixelsize = content.axes_manager[0].scale
        return Sinogram(data, angles, pixelsize)

    def _write_mrc(self, filename, **kwargs):
        raise NotImplementedError

    @staticmethod
    def _read_emi_stack(filename, **kwargs):
        # List all EMI files in the directory of the selected file
        dirname = os.path.dirname(os.path.realpath(filename))
        filenames = glob.glob(dirname + "*.emi")
        # Read the first file for image size and metadata
        im = Image.from_file(filenames[0])
        data = np.zeros((im.data.shape[0], im.data.shape[1], len(filenames)))
        angles = np.zeros(len(filenames))
        # Set the contents of the first file
        data[:, :, 0] = im.data
        angles[0] = im.metadata['alpha_tilt']
        pixelsize = im.pixelsize
        # Loop over the other files to get all the projection images
        for i, filename in enumerate(filenames[1:], start=1):
            im = Image.from_file(filenames[0])
            data[:, :, i] = im.data
            angles[i] = im.metadata['alpha_tilt']
        # Sort the images by tilt angle and return the sinogram
        sorted_indices = np.argsort(angles)
        data = data[:, :, sorted_indices]
        angles = angles[sorted_indices]
        return Sinogram(data, angles, pixelsize)

    _readers = {}
    _writers = {
        'mrc': _write_mrc,
        'ali': _write_mrc,
    }

    def _to_napari_layer(self):
        layer = {}
        layer['data'] = self.data
        layer['name'] = 'Sinogram'
        layer['scale'] = (self.pixelsize, self.pixelsize, 1)
        metadata = {
            'type': TOMOBASE_DATATYPES.SINOGRAM.value(),
            'angles': self.angles
        }
        layer['metadata'] = {'ct metadata': metadata}
        return layer
    
    @classmethod
    def _from_napari_layer(cls, layer):
        if layer.metadata['ct metadata']['type'] != TOMOBASE_DATATYPES.SINOGRAM.value():
            raise ValueError(f'Layer of type {layer.metadata["ct metadata"]["type"]} not recognized')
        sinogram = Sinogram(layer.data, layer.metadata['ct metadata']['angles'], layer.scale[0])
        return sinogram

Sinogram._readers = {
    'mrc': Sinogram._read_mrc,
    'ali': Sinogram._read_mrc,
    'emi': Sinogram._read_emi_stack,
}

