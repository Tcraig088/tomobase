import imageio as iio
def _read_image(filename, **kwargs):
    return ImageStack(proxy.asarray(iio.imread(filename), dtype=float))

def _write_image(self, filename, **kwargs):
    iio.imwrite(filename, self.data)