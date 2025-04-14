from tomobase.registrations.base import ItemDict, ItemDictNonSingleton, Item
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
 
from collections.abc import Iterable
from tomobase.log import logger

from colorama import Fore, Style, init
init(autoreset=True)



class ProcessItemDict(ItemDict):   
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hook = 'is_tomobase_process'
        self._folder = 'processes'
    
    def _update_item(self, obj):
        for key, value in TOMOBASE_TRANSFORM_CATEGORIES.items():
            if value.value == obj.tomobase_category:
                if key not in self._dict:
                    self[key] = ItemDictNonSingleton()
                self[key][obj.tomobase_name] = obj
                TOMOBASE_TRANSFORM_CATEGORIES[key].build_heierarchy(obj.tomobase_subcategories)

    def help(self):
        msg = "\nAvailable processes:\n"
        for key, value in self._dict.items():
            msg += f"\n{Fore.BLUE}Category: {value.name}{Style.RESET_ALL}\n"
            for subkey, subvalue in value.items():
                msg += f"{Fore.GREEN}{subvalue.name}: {subvalue.value.__name__}{Style.RESET_ALL}\n"
                msg += f"{subvalue.value.__doc__}\n"
        logger.info(msg) 
        
TOMOBASE_PROCESSES = ProcessItemDict()
TOMOBASE_PROCESSES.update()
