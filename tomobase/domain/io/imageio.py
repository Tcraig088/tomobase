import imageio as iio

from ...core import proxy
from ...core.data_classes import Image

def _read_image(filename, **kwargs):
    return Image(proxy.asarray(iio.imread(filename), dtype=float))

def _write_image(self, filename, **kwargs):
    iio.imwrite(filename, self.data)

Image.readers['.png'] = _read_image
Image.readers['.jpg'] = _read_image
Image.readers['.tiff'] = _read_image
Image.writers['.png'] = _write_image
Image.writers['.jpg'] = _write_image
Image.writers['.tiff'] = _write_image