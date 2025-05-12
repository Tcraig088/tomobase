import imageio as iio
import stackview
from copy import deepcopy
from IPython.display import display
import collections
collections.Iterable = collections.abc.Iterable
from tomobase.log import logger
from tomobase.registrations.datatypes import TOMOBASE_DATATYPES
from tomobase.registrations.environment import xp


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

    def __init__(self, data, pixelsize=1.0, metadata={}):
        """Create an image

        Arguments:
            data (numpy.ndarray)
                The image. The data is indexed using the
                (rows, columns, channels) standard, which corresponds to
                (y, x, color)
            pixelsize (float)
                The width of the pixels in nanometer (default 1.0)
        """
        self.data = data
        super().__init__(pixelsize, metadata=metadata)
        self.dim_default = 2

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


    def show(self, width = 800, height=800):
        data = self._transpose_to_view()
        self.view = stackview.slice(self.data, display_width=width, display_height=height)
        display(self.view)


    def to_data_tuple(self, attributes:dict={}, metadata:dict={}):
        """_summary_

        Args:
            attributes (dict, optional): _description_. Defaults to {}.
            metadata (dict, optional): _description_. Defaults to {}.

        Returns:
            layerdata: Napari Layer Data Tuple
        """
        logger.debug('Converting Image to Napari Layer Data Tuple: Shape: %s, Pixelsize: %s', self.data.shape, self.pixelsize)
        attributes = attributes
        attributes['name'] = attributes.get('name', 'Image')
        attributes['scale'] = attributes.get('pixelsize' ,(self.pixelsize, self.pixelsize, self.pixelsize))
        attributes['colormap'] = attributes.get('colormap', 'gray')
        attributes['contrast_limits'] = attributes.get('contrast_limits', [0, np.max(self.data)*1.5])
        
        metadata = metadata
        metadata['type'] = TOMOBASE_DATATYPES.IMAGE.value
        metadata['axis'] = ['Signal', 'y', 'x'] if len(self.data.shape) == 3 else ['y', 'x']
        
        for key, value in self.metadata.items():
            metadata[key] = value

        attributes['metadata'] = {'ct metadata': metadata}
        layerdata = (self.data, attributes, 'image')
        
        return layerdata

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


