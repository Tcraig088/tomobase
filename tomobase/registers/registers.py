from typing import List, TypeVar, Generic, Callable, Type, Any
from collections.abc import MutableMapping
from qtpy.QtCore import QObject, Signal
import importlib
import inspect
import os
from functools import partial


from colorama import Fore, Style, init
init(autoreset=True)

from ..data import ImageAbstract, Sinogram, Volume, Image
from ..tiltschemes import TiltScheme
from ..log import logger
from .base import Registry, CategoryRegistry

    
phantoms = Registry(str, Callable)
phantoms._hook = 'is_tomobase_phantom'
phantoms.update(explicit=False)

image_types = Registry(str, ImageAbstract)
image_types['ImageAbstract'] = ImageAbstract
image_types['Sinogram'] = Sinogram
image_types['Volume'] = Volume
image_types['Image'] = Image

tiltschemes = Registry(str, TiltScheme)
tiltschemes._hook = 'is_tomobase_tiltscheme'
tiltschemes.update(explicit=False)

def help_function(name, _dict):
    msg = f"\n{Fore.GREEN} {name} Registration {Style.RESET_ALL}\n" 
    for key, value in _dict.items():
        msg += f"{Fore.BLUE}{key}{Style.RESET_ALL}: {value.__name__}"
        msg += f"{value.__doc__}\n"
        msg += "\n"
    logger.info(msg)
    
phantoms.set_help(partial(help_function, "Phantoms"))
image_types.set_help(partial(help_function, "Image Types"))
tiltschemes.set_help(partial(help_function, "Tilt Schemes"))

 



