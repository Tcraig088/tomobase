import numpy as np
import napari
from napari.qt.threading import thread_worker

from tomobase.core.data_classes import ImageAbstract
from tomobase.utils import set_numpy
from .......tdtomo.domain.controllers import ImageTypeController


@thread_worker
def _compute_fft(model: ImageAbstract):
    #xp = model.data.__array_namespace__()
    xp = np
    f = xp.fft.fftshift(xp.fft.fftn(model.data))
    return set_numpy(xp.log1p(xp.abs(f)))

def fft_init(model: ImageAbstract, viewer=None, **kwargs):
    name = f"{model.process_name} FFT"

    # placeholder layer so init returns a layer immediately
    placeholder = np.zeros((1, 1), dtype=np.float32)
    contrast_limits = kwargs.pop("contrast_limits", (0.0, 1.0))
    layer = napari.layers.Image(placeholder, name=name, contrast_limits=contrast_limits, **kwargs)

    if viewer is not None:
        viewer.add_layer(layer)

    worker = _compute_fft(model)

    @worker.returned.connect
    def _on_done(layer_data):
        # update the existing layer in-place
        layer.data = layer_data
        layer.contrast_limits = (0.0, float(np.max(layer_data) * 2.0))
        layer.refresh()

    worker.start()
    return layer

def fft_update(layer, model: ImageAbstract):
    # async re-compute on updates too (optional)
    worker = _compute_fft(model)

    @worker.returned.connect
    def _on_done(layer_data):
        layer.data = layer_data
        layer.contrast_limits = (0.0, float(np.max(layer_data) * 2.0))
        layer.refresh()

    worker.start()

ImageTypeController.register_renderer("FFT Render", fft_init, fft_update)