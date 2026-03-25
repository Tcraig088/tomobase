import numpy as np
import napari


from tomobase.core.data_classes import ImageAbstract
from tomobase.utils import set_numpy
from .......tdtomo.domain.controllers import ImageTypeController




def _compute_pixel_render(model: ImageAbstract):
    return set_numpy(model.data)

def pixel_init(model: ImageAbstract, viewer=None, **kwargs):
    layer_data = _compute_pixel_render(model)
    name = f"{model.process_name} VolRen"

    contrast_limits = kwargs.pop("contrast_limits", (0, float(np.max(layer_data) * 2.0)))
    layer = napari.layers.Image(layer_data, name=name, contrast_limits=contrast_limits, **kwargs)

    # If you want it added to viewer immediately:
    if viewer is not None:
        viewer.add_layer(layer)
    return layer

def pixel_update(layer, model: ImageAbstract):
    layer.data = _compute_pixel_render(model)
    layer.refresh()


ImageTypeController.register_renderer("Pixel Render", pixel_init, pixel_update)