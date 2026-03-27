import inspect

from .. import registers
from ....core import logger

def _wrap_magicgui(func):
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        func._magicgui = getattr(func, '_magicgui', {})
        for param in sig.parameters.values():
            for key, value in registers.magic_widgets.items():
                if value[1] is not None:
                    if value[1](param.annotation):
                        func._magicgui[param.name] = {"widget_type": value[0]}
                    
                if param.name == 'measurements':
                    func._magicgui[param.name] = {"widget_type": value[0]}
        return func(*args, **kwargs)
    return wrapper






