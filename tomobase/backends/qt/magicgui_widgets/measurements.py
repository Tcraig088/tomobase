from typing import Any, Optional

from magicgui.widgets import  Select
from qtpy.QtCore import Signal

from . import components
from .. import registers

class MeasurementsSelectWidget(components.RegisteredComboBox):
    changed = Signal(object)

    def __init__(
        self,
        *,
        value: Optional[list[Any]] = None,
        **kwargs,
    ):
        for k in ("nullable", "annotation", "gui_only", "bind"):
            kwargs.pop(k, None)

        self.select = Select(label="",choices=[],value=value or [])

        super().__init__(value=value, widgets=[self.select], register= registers.measurements,  **kwargs)

    @property
    def value(self) -> list[Any]:
        try:
            return list(self.select.value)
        except Exception:
            return []

    @value.setter
    def value(self, v: Optional[list[Any]]) -> None:
        try:
            self.select.value = list(v or [])
        except Exception:
            pass

registers.magic_widgets['Measurement'] = (MeasurementsSelectWidget, None)