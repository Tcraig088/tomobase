import os
import glob
import numpy as np
import imageio as iio
import napari

from scipy.io import savemat, loadmat



from qtpy.QtWidgets import QApplication, QFileDialog
import collections
collections.Iterable = collections.abc.Iterable

from abc import ABC, abstractmethod


from tomobase.registrations.environment import TOMOBASE_ENVIRONMENT
if TOMOBASE_ENVIRONMENT.hyperspy:
    import hyperspy.api as hs
    
from tomobase.data.base import Data
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
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


    @staticmethod
    def _read_mat(path):
        obj = loadmat(path)
        #if obj has a series or stack key
        
        if 'series' in obj:
            key = 'series'
        elif 'stack' in obj:
            key = 'stack'
        else:
            key = None
            
        if key is not None:
            d = obj[key]['data'][0][0]
            a = obj[key]['angles'][0][0]
            p = obj[key]['pixelsize'][0][0]
        else:
            d = obj['obj']['data'][0][0]
            a = obj['obj']['angles'][0][0]
            p = obj['obj']['pixelsize'][0][0]

        ts = Sinogram(d.squeeze(), a.squeeze(), p.squeeze())
        return ts
    
    def _write_mrc(self, filename, **kwargs):
        raise NotImplementedError



    def _write_mat(self, filename, **kwargs):
        myrec = {'data':self.data, 'angles':self.angles, 'pixelsize':self.pixelsize} 
        savemat(filename, {'obj': myrec})
    
    
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
        'mat': _write_mat,
        'ali': _write_mrc,
    }

    def _to_napari_layer(self, astuple = True ,**kwargs):
        layer_info = {}
        
        layer_info['name'] = kwargs.get('name', 'Sinogram')
        layer_info['scale'] = kwargs.get('pixelsize' ,(self.pixelsize, self.pixelsize, self.pixelsize))
        metadata = {'type': TOMOBASE_DATATYPES.SINOGRAM.value(),
                    'angles': self.angles}
        
        for key, value in kwargs['viewsettings'].items():
            layer_info[key] = value
            
        for key, value in kwargs.items():
            if key != 'name' and key != 'pixelsize' and key != 'viewsettings':
                metadata[key] = value
        layer_info['metadata'] = {'ct metadata': metadata}
        
        if self.data.ndims == 3:
            self.data.transpose(2,1,0)
        elif self.data.ndims == 4:
            self.data.transpose(2,3,1,0)
        layer = (self.data, layer_info ,'image')
        
        if astuple:
            return layer
        else:
            import napari
            return napari.layers.Layer.create(*layer)
    
    @classmethod
    def _from_napari_layer(cls, layer):
        if layer.metadata['ct metadata']['type'] != TOMOBASE_DATATYPES.SINOGRAM.value():
            raise ValueError(f'Layer of type {layer.metadata["ct metadata"]["type"]} not recognized')
        
        if layer.data.ndims == 3:
            layer.data.transpose(2,1,0)
        elif layer.data.ndims == 4:
            layer.data.transpose(0,2,3,1)
        sinogram = Sinogram(layer.data, layer.metadata['ct metadata']['angles'], layer.scale[0])
        return sinogram

Sinogram._readers = {
    'mrc': Sinogram._read_mrc,
    'ali': Sinogram._read_mrc,
    'emi': Sinogram._read_emi_stack,
    'mat': Sinogram._read_mat,
}

