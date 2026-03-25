
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict
import numpy as np

import napari
from .. import bridges

InitFn = Callable[..., napari.layers.Layer]
UpdateFn = Callable[[napari.layers.Layer, Any], None]  # model is Any/ImageAbstract

@dataclass(frozen=True)
class RendererSpec:
    init: InitFn
    update: UpdateFn

class ImageAbstractController(bridges.QtDataBridge):
    renderers: Dict[str, RendererSpec] = {}
    render_settings_changed = None

    def __init__(self, model, parent=None):
        super().__init__(model, parent)
        self._viewer = None
        self._layers: Dict[str, napari.layers.Layer] = {}
        self._callbacks: Dict[str, Callable[[], None]] = {}
        self._render_settings = {}

        try:
            self._viewer = napari.current_viewer()
        except Exception:
            self._viewer = None

    def get_metadata_dict(self):
        _dict = {}
        _dict['Sample Name'] = self.model.name
        _dict['Process Name'] = self.model.process_name
        _dict['Type'] = type(self.model).__name__
        _dict['Pixel Size (nm)'] = self.model.pixel_size

        _data_dict = {}
        _data_dict['Shape'] = self.model.values.shape
        _data_dict['Dtype'] = self.model.values.dtype
        _data_dict['Min'] = np.round(float(np.min(self.model.data)), 2)
        _data_dict['Max'] = np.round(float(np.max(self.model.data)), 2)
        _data_dict['axis'] = self.model.data.dims

        _dict['layers'] = {layer.name: type(layer).__name__ for layer in self._layers.values()}
        _dict['Data'] = _data_dict
        _dict['Metadata'] = self.model.metadata
        return {self.model.process_name: _dict}


    @classmethod
    def register_renderer(cls, name: str, init: InitFn, update: UpdateFn) -> None:
        cls.renderers[name] = RendererSpec(init=init, update=update)

    def add_render(self, name: str, **kwargs) -> napari.layers.Layer:
        """Create the layer and wire it to model.data_changed."""
        if name not in self.renderers:
            raise KeyError(f"Unknown renderer '{name}'. Available: {list(self.renderers)}")

        spec = self.renderers[name]

        # 1) create/init the layer (any layer type)
        layer = spec.init(self.model, viewer=self._viewer, **kwargs)
        self._layers[layer.name] = layer

        # 2) connect update callback and keep a reference so we can disconnect later
        cb = lambda l=layer, m=self.model, u=spec.update: u(l, m)
        self._callbacks[layer.name] = cb
        self.model.data_changed.connect(cb)

        return layer

    def _on_layer_removed(self, event) -> None:
        """Disconnect updates when the user deletes a layer."""
        layer = event.value
        if layer is None:
            return

        name = layer.name
        cb = self._callbacks.pop(name, None)
        if cb is not None:
            try:
                self.model.data_changed.disconnect(cb)
            except Exception:
                pass

        self._layers.pop(name, None)

    def close(self) -> None:
        """Call when controller is destroyed/unloaded."""
        if self._viewer is not None:
            try:
                self._viewer.layers.events.removed.disconnect(self._on_layer_removed)
            except Exception:
                pass

        for name, cb in list(self._callbacks.items()):
            try:
                self.model.data_changed.disconnect(cb)
            except Exception:
                pass

        self._callbacks.clear()
        self._layers.clear()






        
        