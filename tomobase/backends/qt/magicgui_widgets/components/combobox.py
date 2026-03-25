from typing import Any, Optional
from magicgui.widgets import Container
from qtpy.QtCore import QTimer

from .....core import logger

class RegisteredComboBox(Container):
    def __init__(
        self,
        *,
        value: Optional[Any] = None,
        widgets: Any = None,
        register: Any = None,
        **kwargs,
    ):
        for k in ("nullable", "annotation", "gui_only", "bind"):
            kwargs.pop(k, None)

        self.widgets = widgets
        self.register = register
        super().__init__(widgets=self.widgets, layout="vertical", **kwargs)

        self.refresh_choices()
        self.connect()

        if value is not None and value is not ...:
            self.value = value

        self.native.destroyed.connect(self._cleanup)

    def refresh_choices(self, *args):
        # make sure UI update happens on Qt event loop / main thread
        QTimer.singleShot(0, self._refresh_choices_impl)

    def _refresh_choices_impl(self):
        combo = self.widgets[0]
        current_value = combo.value
        
        
        choices = [(n, v.model) for n, v in self.register.items()]
        logger.debug(f"Refreshing choices for {self.register}: current value = {choices}")
        combo.choices = list(choices)

        if not choices:
            # important: clear value explicitly
            try:
                combo.value = None
            except Exception:
                pass
            return

        # try to preserve current selection if it still exists
        valid_values = [v for _, v in choices]
        if current_value in valid_values:
            combo.value = current_value
        else:
            combo.value = valid_values[0]

    @property
    def value(self):
        combo = self.widgets[0]
        if not combo.choices:
            return None
        return combo.value

    @value.setter
    def value(self, v):
        combo = self.widgets[0]

        if v is ...:
            return

        if not combo.choices:
            return

        valid_values = [val for _, val in combo.choices]

        if v in valid_values:
            combo.value = v
        else:
            # optional: fallback instead of silent fail
            combo.value = valid_values[0]

    def connect(self):
        self.register.updated.connect(self.refresh_choices)
        self.register.removed.connect(self.refresh_choices)
        self.register.added.connect(self.refresh_choices)

    def _cleanup(self):
        try:
            self.register.updated.disconnect(self.refresh_choices)
            self.register.removed.disconnect(self.refresh_choices)
            self.register.added.disconnect(self.refresh_choices)
        except Exception:
            pass