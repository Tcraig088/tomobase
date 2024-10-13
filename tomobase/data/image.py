import numpy as np
import imageio as iio
import napari

from qtpy.QtWidgets import QApplication, QFileDialog
import collections
collections.Iterable = collections.abc.Iterable

from abc import ABC, abstractmethod
import sys

from tomobase.registrations.environment import TOMOBASE_ENVIRONMENT
if TOMOBASE_ENVIRONMENT.hyperspy:
    import hyperspy.api as hs

from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.data.base import Data

class Image(Data):
    """An image
    Attributes:
        data (numpy.ndarray)
            The image. The data is indexed using the (rows, columns, channels)
            standard, which corresponds to (y, x, color)
        pixelsize (float)
            The width of the pixels in nanometer
        metadata (dict)
            A dictionary with additional metadata, the contents of this
            attribute depend on from which file they were read
    """

    def __init__(self, data, pixelsize=1.0):
        """Create an image

        Arguments:
            data (numpy.ndarray)
                The image. The data is indexed using the
                (rows, columns, channels) standard, which corresponds to
                (y, x, color)
            pixelsize (float)
                The width of the pixels in nanometer (default 1.0)
        """
        super().__init__(data, pixelsize)
        self.metadata = {}

    @staticmethod
    def _read_emi(filename, **kwargs):
        # TODO make this method independent of Hyperspy
        content = hs.load(filename, lazy=False, reader='emi')
        data = np.transpose(np.asarray(content.data, dtype=float), (1, 0))   # With transpose we make sure that
                                                                # the orientation is correct in the
                                                                # case where the scanning rotation
                                                                # was set to -90 (which is the
                                                                # default of the FEI tomo software)
        pixelsize = content.axes_manager[0].scale  # Hyperspy uses nm
        im = Image(data, pixelsize)
        im.metadata['alpha_tilt'] = content.metadata.Acquisition_instrument.TEM.Stage.tilt_alpha
        return im

    @staticmethod
    def _read_image(filename, **kwargs):
        return Image(np.asarray(iio.imread(filename), dtype=float))

    def _write_image(self, filename, **kwargs):
        iio.imwrite(filename, self.data)

    def _to_napari_layer(self):
        layer = {}
        layer['data']= self.data
        layer['name'] =  'Image'
        layer['scale'] = (self.pixelsize, self.pixelsize)
        metadata = {
            'type': TOMOBASE_DATATYPES.IMAGE,
            'metadata': self.metadata
        }
        layer['metadata'] = {'ct metadata': metadata}
        return layer
    
    def _to_napari_layer(self, astuple = True ,**kwargs):
        layer_info = {}
        
        layer_info['name'] = kwargs.get('name', 'Image')
        layer_info['scale'] = kwargs.get('pixelsize' ,(self.pixelsize, self.pixelsize))
        metadata = {'type': TOMOBASE_DATATYPES.IMAGE.value(),
                    'metadata': self.metadata}
        
        for key, value in kwargs['viewsettings'].items():
            layer_info[key] = value
            
        for key, value in kwargs.items():
            if key != 'name' and key != 'pixelsize' and key != 'viewsettings':
                metadata[key] = value
        layer_info['metadata'] = {'ct metadata': metadata}
        
        if self.data.ndims == 3:
            self.data.transpose(2,1,0)
        layer = (self.data, layer_info ,'image')
        
        if astuple:
            return layer
        else:
            import napari
            return napari.layers.Layer.create(*layer)
    
    @classmethod
    def _from_napari_layer(cls, layer):
        if layer.metadata['ct metadata']['type'] != TOMOBASE_DATATYPES.IMAGE:
            raise ValueError(f'Layer of type {layer.metadata["ct metadata"]["type"]} not recognized')
        if layer.data.ndims == 3:
            layer.data.transpose(2,1,0)
        image = Image(layer.data, layer.scale[0])
        image.metadata = layer.metadata['ct metadata']['metadata']
        return image

    _readers = {}
    _writers = {
        'png': _write_image,
        'bmp': _write_image,
        'tif': _write_image,
        'tiff': _write_image,
    }


Image._readers = {
    'emi': Image._read_emi,
    'png': Image._read_image,
    'bmp': Image._read_image,
    'tif': Image._read_image,
    'tiff': Image._read_image,
}


