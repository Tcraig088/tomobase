
from pathlib import Path
import copy

import numpy as np

from ...core.data_classes.images import Volume

def _write_rec(self, filename, normalize=True, **kwargs):
    # Convert data to (X, Y, Z)
    data = np.transpose(self.values, (1, 0, 2))

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
    dimensions = self.pixel_size * np.array(data.shape, dtype='float32')
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


def _read_rec(filename, normalize=True, **kwargs):
        if isinstance(filename, str):
            filename = Path(filename)
        kwargs['name'] = kwargs.get('name', filename.parent.name)
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
            name = kwargs.get('name', filename.stem)
            if normalize:
                return _rescale(Volume(name, data.astype(float), pixelsize=1.0))
            else:
                
                return Volume(name, data, pixelsize)
            
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


Volume.readers['.rec'] = _read_rec
Volume.writers['.rec'] = _write_rec