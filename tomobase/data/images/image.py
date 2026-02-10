import imageio as iio

from copy import deepcopy
import collections
collections.Iterable = collections.abc.Iterable

from ...log import logger
from .base import BaseImageModel

class Image(BaseImageModel):

    def __init__(self, data, pixelsize: float = 1.0, metadata: dict = {}, *args, **kwargs):
        super().__init__(data, pixelsize, metadata=metadata, *args, **kwargs)

    @staticmethod
    def _read_image(filename, **kwargs):
        return Image(proxy.asarray(iio.imread(filename), dtype=float))

    def _write_image(self, filename, **kwargs):
        iio.imwrite(filename, self.data)

    readers = {}
    writers = {
        'png': _write_image,
        'bmp': _write_image,
        'tif': _write_image,
        'tiff': _write_image,
    }

    def _copy_from(self, other='Image'):
        return super()._copy_from(other=other)
    
    def _deepcopy_from(self, other='Image', memo:dict={}):
        return super()._deepcopy_from(other=other, memo=memo)
    
Image.readers = {
    'png': Image._read_image,
    'bmp': Image._read_image,
    'tif': Image._read_image,
    'tiff': Image._read_image,
}


