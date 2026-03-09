import imageio as iio

from copy import deepcopy
import collections
collections.Iterable = collections.abc.Iterable

from ...log import logger
from .base import Image

class ImageStack(Image):

    def __init__(self, data, pixelsize: float = 1.0, metadata: dict = {}, *args, **kwargs):
        super().__init__(data, pixelsize, metadata=metadata, *args, **kwargs)

    @staticmethod
    def _read_image(filename, **kwargs):
        return ImageStack(proxy.asarray(iio.imread(filename), dtype=float))

    def _write_image(self, filename, **kwargs):
        iio.imwrite(filename, self.data)

    readers = {}
    writers = {
        'png': _write_image,
        'bmp': _write_image,
        'tif': _write_image,
        'tiff': _write_image,
    }

    def _copy_from(self, other='ImageStack'):
        return super()._copy_from(other=other)
    
    def _deepcopy_from(self, other='ImageStack', memo:dict={}):
        return super()._deepcopy_from(other=other, memo=memo)
    
ImageStack.readers = {
    'png': ImageStack._read_image,
    'bmp': ImageStack._read_image,
    'tif': ImageStack._read_image,
    'tiff': ImageStack._read_image,
}


