import numpy as np
import copy
from copy import deepcopy

import collections
collections.Iterable = collections.abc.Iterable

from tomobase.log import logger  
from tomobase.data.base import Data 
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.data.image import Image

import stackview
import ipywidgets as widgets
from IPython.display import display

def _rescale(data, lower=0, upper=1, inplace=True):
    """Rescale data by scaling it to a given range.

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

    def __init__(self, data, pixelsize=1.0, metadata = {}):
        """Create a volume
        Arguments:
            data (numpy.ndarray)
                The data represented by voxels. The data is indexed using the
                (rows, columns, slices) standard, which corresponds to (y, x, z)
            pixelsize (float)
                The width of the voxels in nanometer (default 1.0)
        """
        self.data = data
        super().__init__(pixelsize, metadata)
    
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
                return _rescale(Volume(data.astype(float), pixelsize=1.0))
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
        header[10:13] = dimensions.view('int32')

        data = data.flatten(order='F')
        if normalize:
            data = data.astype(np.float32)
            data -= data.min()
            data *= 255 / data.max()
            data = data.astype('uint8')

        with open(filename, 'wb') as f:
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


    def to_data_tuple(self, attributes:dict={}, metadata:dict={}):
        """_summary_

        Args:
            attributes (dict, optional): _description_. Defaults to {}.
            metadata (dict, optional): _description_. Defaults to {}.

        Returns:
            layerdata: Napari Layer Data Tuple
        """
        logger.debug('Converting Volume to Napari Layer Data Tuple: Shape: %s, Pixelsize: %s', self.data.shape, self.pixelsize)
        attributes = attributes
        attributes['name'] = attributes.get('name', 'Volume')
        attributes['colormap'] = 'magma'  
        attributes['rendering'] = 'attenuated_mip'
        attributes['contrast_limits'] = attributes.get('contrast_limits', [0, np.max(self.data)*1.5])
        
        metadata = metadata
        metadata['type'] = TOMOBASE_DATATYPES.VOLUME.value
        metadata['axis'] = ['Projection', 'y', 'x'] if len(self.data.shape) == 3 else ['Projection', 'Signal', 'y', 'x']
        
        for key, value in self.metadata.items():
            metadata[key] = value

        attributes['metadata'] = {'ct metadata': metadata}
        layerdata = (self.data, attributes, 'image')
        
        return layerdata
    
    @classmethod
    def from_data_tuple(cls, layerdata, attributes=None):
        if attributes is None:
            data = layerdata.data
            scale = layerdata.scale[0]
            layer_metadata = layerdata.metadata
        else:
            data = layerdata
            scale = attributes['scale'][0]
            layer_metadata = attributes['metadata']

        layer_metadata = deepcopy(layer_metadata)
        metadata = layer_metadata['ct metadata']
        metadata.pop('axis')
        metadata.pop('type')

        return cls(data, scale, metadata)

    def show(self, display_width=800, display_height=800):
        """shows the sinogram in a stackview window

        Returns:
            _type_: _description_
        """
        data = self._transpose_to_view(use_copy=True)
        display(stackview.orthogonal(data, display_width=display_width, display_height=display_height))
    
Volume._readers = {
    'rec': Volume._read_rec,
    'tif': Volume._read_tiff,
    'tiff': Volume._read_tiff,
}
