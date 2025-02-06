import numpy as np
import imageio as iio
import stackview
from copy import deepcopy
from IPython.display import display
import collections
collections.Iterable = collections.abc.Iterable

from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.registrations.environment import TOMOBASE_ENVIRONMENT
if TOMOBASE_ENVIRONMENT.hyperspy:
    import hyperspy.api as hs

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


    def _transpose_to_view(self, use_copy=False, data=None):
        """ Transpose the data from the standard orientation for data processessing to the view orientation.
        """
        if use_copy:
            data = deepcopy(self.data)
            if len(data.shape) == 3:
                data = data.transpose(2,1,0)
            return data

        if data is not None:
            if len(data.shape) == 3:
                data = data.transpose(2,1,0)
            return data
            
        if len(self.data.shape) == 3:
            self.data = self.data.transpose(2,1,0)

        return self.data
            
    @classmethod
    def _transpose_from_view(cls, data):
        """ Transpose the data from the view orientation to the standard orientation for data processessing.
        """
        if len(data.shape) == 3:
            data = data.transpose(2,1,0)
        return data
    
    def show(self, width = 800, height=800):
        data = self._transpose_to_view()
        self.view = stackview.slice(self.data, display_width=width, display_height=height)
        display(self.view)




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


