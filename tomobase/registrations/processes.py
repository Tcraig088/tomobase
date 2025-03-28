from tomobase.registrations.base import ItemDict
from tomobase.registrations.transforms import TOMOBASE_TRANSFORM_CATEGORIES
 
from collections.abc import Iterable

class ProcessItemDict(ItemDict):   
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hook = 'is_tomobase_process'
        self._folder = 'processes'
    
    def _update_item(self, obj):
        if isinstance(obj.tomobase_category, Iterable):
            for category in obj.tomobase_category:
                for key, value in TOMOBASE_TRANSFORM_CATEGORIES.items():
                    if TOMOBASE_TRANSFORM_CATEGORIES[key].value() == category:
                        self._dict[key][obj.tomobase_name] = obj
                        TOMOBASE_TRANSFORM_CATEGORIES[key].append(obj.tomobase_subcategories)
    
        else:
            for key, value in TOMOBASE_TRANSFORM_CATEGORIES.items():
                if TOMOBASE_TRANSFORM_CATEGORIES[key].value() == obj.tomobase_category:
                    self._dict[key][obj.tomobase_name] = obj
                    TOMOBASE_TRANSFORM_CATEGORIES[key].append(obj.tomobase_subcategories)
    

TOMOBASE_PROCESSES = ProcessItemDict()
TOMOBASE_PROCESSES.update()

TOMOBASE_PROCESSES.help()