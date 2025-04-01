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
        logger.info(f"Item to be added: {obj.tomobase_name}")
        for key, value in TOMOBASE_TRANSFORM_CATEGORIES.items():
            logger.info(f"Checking category: {key}, {value.name} {value.value} {obj.tomobase_category}")
            if value.value == obj.tomobase_category:
                print('Confirmed', key, value.value, obj.tomobase_category)
                if key not in self._dict:
                    self[key] = ItemDictNonSingleton()
                self._dict[key][obj.tomobase_name] = obj
                TOMOBASE_TRANSFORM_CATEGORIES[key] = obj.tomobase_subcategories
                
            if isinstance(obj.tomobase_category, Iterable):
                logger.info(f"Checking category (iterable): {key}, {value.name} {value.value} {obj.tomobase_category}")
                for category in obj.tomobase_category:
                    if category == value.value:
                        if key not in self._dict:
                            self[key] = ItemDictNonSingleton()
                        self._dict[key][obj.tomobase_name] = obj
                        TOMOBASE_TRANSFORM_CATEGORIES[key] = obj.tomobase_subcategories
    
    def help(self):
        for key, value in self._dict.items():
            logger.info(f"Category: {key}")
            for subkey, subvalue in value.items():
                logger.info(f"  {subkey.name}: {subvalue.value}")
                logger.info(f"    {subvalue.value.__doc__}")
         
TOMOBASE_PROCESSES = ProcessItemDict()
TOMOBASE_PROCESSES.update()
