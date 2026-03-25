from typing import  Union,  get_origin, get_args, Optional
from types import UnionType
from magicgui.widgets import ComboBox
import inspect


from . import components
from .. import registers
from ....core import base_classes

class ImageComboBoxWidget(components.RegisteredComboBox):
    def __init__(
        self,
        *,
        value: Optional[base_classes.ImageAbstract] = None,
        **kwargs,
    ):
        for k in ("nullable", "annotation", "gui_only", "bind"):
            kwargs.pop(k, None)

        self.register = registers.images
        self.dropbox = ComboBox(label="", choices=[])

        super().__init__(value=value, widgets=[self.dropbox], register=registers.images, **kwargs)

def _is_none_type(x):
    return x is type(None)


def _is_union(annotation):
    return get_origin(annotation) in (Union, UnionType)


def _is_image_class(annotation):
    return inspect.isclass(annotation) and issubclass(annotation, base_classes.ImageAbstract)


def _validate_image_widget(annotation):
    # plain class: ImageAbstract or subclass
    if _is_image_class(annotation):
        return True

    # Union[...] or X | Y
    if _is_union(annotation):
        args = [a for a in get_args(annotation) if not _is_none_type(a)]
        return len(args) > 0 and all(_is_image_class(a) for a in args)

    return False
    
registers.magic_widgets['Image'] = (ImageComboBoxWidget, _validate_image_widget)