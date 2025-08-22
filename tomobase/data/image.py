import imageio as iio

from copy import deepcopy
import collections
collections.Iterable = collections.abc.Iterable

from ..log import logger
from ..registrations.datatypes import TOMOBASE_DATATYPES
from ..registrations.environment import xp
from .base import Data

class Image(Data):
    """ A class for single image datasets.

    Supported File Formats:
        - .png
        - .jpg
        - .jpeg
        - .bmp
        - .tif
        - .tiff

    Attributes:
        data (numpy.ndarray | cupy.ndarray): The image data. The data is indexed using the (rows, columns, channels) standard, which corresponds to (x, y, color)
    """

    def __init__(self, data, pixelsize: float = 1.0, metadata: dict = {}):
        """
        Initialize the Image object

        Args:
            data (numpy.ndarray) : the image data
            pixelsize (float): The size of the pixels in the dataset. Defaults to 1.0 nm
            metadata (dict): A dictionary containing metadata about the dataset. Defaults to {}.
        """

        self.data = data
        super().__init__(pixelsize, metadata=metadata)

    @staticmethod
    def _read_emi(filename, **kwargs):
        # TODO make this method independent of Hyperspy
        """
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
        """

    @staticmethod
    def _read_image(filename, **kwargs):
        return Image(xp.asarray(iio.imread(filename), dtype=float))

    def _write_image(self, filename, **kwargs):
        iio.imwrite(filename, self.data)

    def layer_metadata(self, metadata={}):
        meta = super().layer_metadata(metadata)
        meta['ct metadata']['type'] = TOMOBASE_DATATYPES.IMAGE.value
        meta['ct metadata']['axis'] = ['Signal', 'y', 'x'] if len(self.data.shape) == 3 else ['y', 'x']
        return meta

    def layer_attributes(self, attributes={}):
        attr = super().layer_attributes(attributes)
        attr['name'] = attr.get('name', 'Image')
        attr['scale'] = attr.get('pixelsize' ,(self.pixelsize, self.pixelsize))
        attr['contrast_limits'] = attr.get('contrast_limits', [0, np.max(self.data)*1.5])
        return attr


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


