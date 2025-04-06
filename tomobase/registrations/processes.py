from tomobase.registrations.base import ItemDict, ItemDictNonSingleton, Item
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
 
from collections.abc import Iterable
from tomobase.log import logger


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
                TOMOBASE_TRANSFORM_CATEGORIES[key] = obj.tomobase_subcategories
                
            if isinstance(obj.tomobase_category, Iterable):
                for category in obj.tomobase_category:
                    if category == value.value:
                        if key not in self._dict:
                            self[key] = ItemDictNonSingleton()
                        self[key][obj.tomobase_name] = obj
                        TOMOBASE_TRANSFORM_CATEGORIES[key] = obj.tomobase_subcategories
    
    def help(self):
        msg = "\nAvailable processes:\n"
        for key, value in self._dict.items():
            msg += f"\nCategory: {value.name}:\n"
            for subkey, subvalue in value.items():
                msg += f"{subvalue.name}: {subvalue.value}\n"
                msg += f"{subvalue.value.__doc__}\n"
        logger.info(msg) 
        
TOMOBASE_PROCESSES = ProcessItemDict()
TOMOBASE_PROCESSES.update()
