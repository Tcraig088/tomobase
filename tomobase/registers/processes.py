

from typing import Callable
from .base import Registry, CategoryRegistry
from ..log import logger
from colorama import Fore, Style, init
init(autoreset=True)

processes = Registry(str, Callable)
processes._hook = 'is_tomobase_process'
processes.update(explicit=False)

def help_processes(_dict):
    msg = f"\n{Fore.GREEN} Processes Registration {Style.RESET_ALL}\n" 
    
    items = sorted(_dict._data.items(), key=lambda kv: int(getattr(kv[1], 'tomobase_category', 0)))
    
    for key, value in _dict.items():
        msg += f"{Fore.BLUE}{key}{Style.RESET_ALL}: {value.__name__} (Category: {getattr(value, 'tomobase_category', 'N/A')})"
        doc = value.__doc__.strip() if value.__doc__ else "No description"
        msg += f"\n{doc}\n"
        
    logger.info(msg)
        
processes.set_help(help_processes)