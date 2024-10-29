import inspect
from tomobase.log import logger
from qtpy.QtWidgets import QWidget, QVBoxLayout, QLabel, QCheckBox, QComboBox, QGridLayout, QSpinBox, QDoubleSpinBox, QLineEdit


def connect(widget: QWidget, func):
    if isinstance(widget, QSpinBox):
        widget.valueChanged.connect(func)
    elif isinstance(widget, QDoubleSpinBox):
        widget.valueChanged.connect(func)
    elif isinstance(widget, QLineEdit):
        widget.textChanged.connect(func)
    elif isinstance(widget, QCheckBox):
        widget.stateChanged.connect(func)
    else:
        logger.warning(f'Widget {widget} has an unsupported type')

def get_value(widget: QWidget):
    if isinstance(widget, QSpinBox):
        return widget.value()
    elif isinstance(widget, QDoubleSpinBox):
        return widget.value()
    elif isinstance(widget, QLineEdit):
        return widget.text()
    elif isinstance(widget, QCheckBox):
        return widget.isChecked()
    else:
        logger.warning(f'Widget {widget} has an unsupported type')

def get_widget(name: str, param):
    label = QLabel(name.capitalize().replace("_", " "))
    isdefault = True
    if param.default == inspect.Parameter.empty:
        isdefault = False
    if param.annotation == int:
        widget = QSpinBox()
        widget.setRange(0, 1000000)
        widget.setValue(param.default)
        if isdefault:
            widget.setValue(param.default)
    elif param.annotation == float:
        widget = QDoubleSpinBox()
        widget.setRange(-10000000, 1000000)
        widget.setSingleStep(0.01) 
        if isdefault:
            widget.setValue(param.default)
    elif param.annotation == str:
        widget = QLineEdit()
        widget.setText(param.default)
        if isdefault:
            widget.setText(param.default)
    elif param.annotation == bool:
        widget = QCheckBox()
        widget.setChecked(param.default)
        if isdefault:
            widget.setChecked(param.default)
    else:
        logger.warning(f'Parameter {name} has an unsupported type')
        return None, None, None
    return name, label, widget