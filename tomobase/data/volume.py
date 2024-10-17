import numpy as np
import copy

import collections
collections.Iterable = collections.abc.Iterable

from abc import ABC, abstractmethod

from tomobase.registrations.environment import TOMOBASE_ENVIRONMENT
if TOMOBASE_ENVIRONMENT.hyperspy:
    import hyperspy.api as hs
    
    
from tomobase.data.base import Data 
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.data.image import Image


def _rescale(data, lower=0, upper=1, inplace=True):
    """Rescale data by scaling it to a given range. Private version for internal use only.

    Arguments:
        data (Image, Volume or Sinogram)
            The data to rescale
        lower (float)
            The lower bound of the rescaled data
        upper (float)
            The upper bound of the rescaled data
        inplace (bool)
            Whether to do the rescaling in-place in the input data object

    Returns:
        Image, Volume or Sinogram
            The result
    """
    if not inplace:
        data = copy(data)

    minValue = data.data.min()
    maxValue = data.data.max()

    if minValue == maxValue:
        raise ValueError('Cannot normalize a uniform array.')

    data.data -= minValue
    data.data *= (upper - lower) / (maxValue - minValue)
    data.data += lower

    return data

class Volume(Data):
    """A 3D volume that is the result of a tomographic reconstruction

    Attributes:
        data (numpy.ndarray)
            The data represented by voxels. The data is indexed using the
            (rows, columns, slices) standard, which corresponds to (y, x, z)
        pixelsize (float)
            The width of the voxels in nanometer
    """

    def __init__(self, data, pixelsize=1.0):
        """Create a volume
        Arguments:
            data (numpy.ndarray)
                The data represented by voxels. The data is indexed using the
                (rows, columns, slices) standard, which corresponds to (y, x, z)
            pixelsize (float)
                The width of the voxels in nanometer (default 1.0)
        """
        super().__init__(data, pixelsize)

    @staticmethod
    def _read_rec(filename, normalize=True, **kwargs):
        with open(filename, 'rb') as f:
            # Data dimensions and type
            nx, ny, nz = np.fromfile(f, count=3, dtype='int32')
            datatype = np.fromfile(f, count=1, dtype='int32')
            if datatype == 0:
                datatype = 'uint8'
            elif datatype == 1:
                datatype = 'int16'
            elif datatype == 2:
                datatype = 'float32'
            elif datatype == 6:
                datatype = 'uint16'
            else:
                raise ValueError("Unsupported datatype in REC data.")

            # Pixel size in nm
            f.seek(10)
            cell_size = np.fromfile(f, count=1, dtype='int32')
            pixelsize = cell_size.astype('float32') / nx

            # Skip header
            f.seek(92)
            header_size = np.fromfile(f, count=1, dtype='int32')
            f.seek(1024 + header_size.item())

            # Read data
            data = np.fromfile(f, count=nx*ny*nz, dtype=datatype)
            data = np.reshape(data, [nx, ny, nz], order='F')
            data = np.transpose(data, (1, 0, 2))

            if normalize:
                return _rescale(Volume(data.astype(float), pixelsize))
            else:
                return Volume(data, pixelsize)

    def _write_rec(self, filename, normalize=True, **kwargs):
        # Convert data to (X, Y, Z)
        data = np.transpose(self.data, (1, 0, 2))

        # Create MRC header
        header = np.zeros(256, dtype='int32')
        header[:3] = data.shape  # Array dimensions
        if data.dtype == np.uint8 or normalize:
            header[3] = 0
        elif data.dtype == np.int16:
            header[3] = 1
        elif data.dtype == np.float32:
            header[3] = 2
        elif data.dtype == np.uint16:
            header[3] = 6
        else:
            raise TypeError("Unsupported data type for writing in REC file.")
        # Sampling along X, Y and Z. Same as array dimensions
        header[7:10] = data.shape
        # Physical dimensions in nm. Preserve float32 data type
        dimensions = self.pixelsize * np.array(data.shape, dtype='float32')
        header[10:13] = dimensions.view(dtype='int32')

        data = data.flatten(order='F')
        if normalize:
            data -= data.min()
            data *= 255 / data.max()
            data = data.astype('uint8')

        with open(filename, 'w') as f:
            header.tofile(f)
            data.tofile(f)

    @staticmethod
    def _read_tiff(filename, **kwargs):
        raise NotImplementedError

    def _write_tiff(self, filename, **kwargs):
        raise NotImplementedError

    _readers = {}
    _writers = {
        'rec': _write_rec,
        'tif': _write_tiff,
        'tiff': _write_tiff,
    }

    def _to_napari_layer(self, astuple = True ,**kwargs):
        layer_info = {}
        
        layer_info['name'] = kwargs.get('name', 'Volume')
        layer_info['scale'] = kwargs.get('pixelsize' ,(self.pixelsize, self.pixelsize, self.pixelsize))
        metadata = {'type': TOMOBASE_DATATYPES.VOLUME.value()}
        for key, value in kwargs['viewsettings'].items():
            layer_info[key] = value
            
        for key, value in kwargs.items():
            if key != 'name' and key != 'pixelsize' and key != 'viewsettings':
                metadata[key] = value
                
        if len(self.data.shape) == 3:
            self.data = self.data.transpose(2,0,1)
            metadata['axis_labels'] = ['z', 'y', 'x']
        elif len(self.data.shape) == 4:
            self.data = self.data.transpose(2,3,0,1)
            metadata['axis_labels'] = ['Signals','z', 'y', 'x']
        
        layer_info['metadata'] = {'ct metadata': metadata}  
        layer = [self.data, layer_info ,'image']
        
        if astuple:
            return layer
        else:
            import napari
            napari.layer.Layer.create(*layer)
    
    @classmethod
    def _from_napari_layer(cls, layer):
        if layer.metadata['ct metadata']['type'] != TOMOBASE_DATATYPES.VOLUME.value():
            raise ValueError(f'Layer of type {layer.metadata["ct metadata"]["type"]} not recognized')
        
        if len(layer.data.shape) == 3:
            data = layer.data.transpose(1,2,0)
        elif len(layer.data.shape) == 4:
            data = layer.data.transpose(2, 3, 0, 1)
        volume = Volume(data, layer.scale[0])
        return volume
    
Volume._readers = {
    'rec': Volume._read_rec,
    'tif': Volume._read_tiff,
    'tiff': Volume._read_tiff,
}
