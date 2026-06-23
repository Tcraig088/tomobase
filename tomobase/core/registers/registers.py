from typing import  Callable
from functools import partial

from colorama import Fore, Style, init
init(autoreset=True)

from ..log import logger
from ..base_classes.registers import Registry

from ..base_classes import ImageAbstract, TiltSchemeAbstract, MeasurementAbstract
from .categories import categories
    
modules = Registry(str, Callable)
images = Registry(str, ImageAbstract)
tiltschemes = Registry(str, TiltSchemeAbstract)
procedures = Registry(str, Callable)
measurements = Registry(str, MeasurementAbstract)
    
procedures.set_hierarchy(categories, categories['Tomography'])

def help_function(name, _dict):
    msg = f"\n{Fore.GREEN} {name} Registration {Style.RESET_ALL}\n" 
    for key, value in _dict.items():
        msg += f"{Fore.BLUE}{key}{Style.RESET_ALL}: {value.__name__}"
        msg += f"{value.__doc__}\n"
        msg += "\n"
    logger.info(msg)
    
def help_processes(_dict):
    msg = f"\n{Fore.GREEN} Processes Registration {Style.RESET_ALL}\n" 
    
    items = sorted(_dict._data.items(), key=lambda kv: int(getattr(kv[1], 'tomobase_category', 0)))
    
    for key, value in _dict.items():
        msg += f"{Fore.BLUE}{key}{Style.RESET_ALL}: {value.__name__} (Category: {getattr(value, 'tomobase_category', 'N/A')})"
        doc = value.__doc__.strip() if value.__doc__ else "No description"
        msg += f"\n{doc}\n"
        
    logger.info(msg)


images.set_help(partial(help_function, "Image Types"))
tiltschemes.set_help(partial(help_function, "Tilt Schemes"))     
procedures.set_help(help_processes)
measurements.set_help(partial(help_function, "Measurements"))

