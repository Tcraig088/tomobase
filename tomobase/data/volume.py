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
        super().__init__(data, pixelsize, metadata)

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

    def _transpose_to_view(self, use_copy=False, data=None):
        """ Transpose the data from the standard orientation for data processessing to the view orientation.
        """
        if use_copy:
            data = deepcopy(self.data)
            if len(data.shape) == 3:
                data = data.transpose(2,1,0)
            elif len(data.shape) == 4:
                data = data.transpose(2,3,1,0)
            return data
        
        if data is not None:
            if len(data.shape) == 3:
                data = data.transpose(2,1,0)
            elif len(data.shape) == 4:
                data = data.transpose(2,3,1,0)
            return data
        
        if len(self.data.shape) == 3:
            self.data = self.data.transpose(2,1,0)
        elif len(self.data.shape) == 4:
            self.data = self.data.transpose(2,3,1,0)
        return self.data
            
    @classmethod
    def _transpose_from_view(cls, data):
        """ Transpose the data from the view orientation to the standard orientation for data processessing.
        """
        if len(data.shape) == 3:
            data = data.transpose(2,1,0)
        else:
            data = data.transpose(3,2,0,1)
        return data
    
    def to_data_tuple(self, attributes:dict={}, metadata:dict={}):
        """_summary_

        Args:
            attributes (dict, optional): _description_. Defaults to {}.
            metadata (dict, optional): _description_. Defaults to {}.

        Returns:
            layerdata: Napari Layer Data Tuple
        """
        logger.debug('Converting Sinogram to Napari Layer Data Tuple: Shape: %s, Angles: %s, Pixelsize: %s', self.data.shape, self.angles, self.pixelsize)
        attributes = attributes
        attributes['name'] = attributes.get('name', 'Volume')
        attributes['colormap'] = 'magma'  
        attributes['rendering'] = 'attenuated_mip'
        attributes['contrast_limits'] = attributes.get('contrast_limits', [0, np.max(self.data)*1.5])
        
        metadata = metadata
        metadata['type'] = TOMOBASE_DATATYPES.Volume.value()
        metadata['axis'] = ['Projection', 'y', 'x'] if len(self.data.shape) == 3 else ['Projection', 'Signal', 'y', 'x']
        
        for key, value in self.metadata.items():
            metadata[key] = value

        attributes['metadata'] = {'ct metadata': metadata}
        self.data = self._transpose_to_view()
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

        return cls(cls._transpose_from_view(data), scale, metadata)

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
