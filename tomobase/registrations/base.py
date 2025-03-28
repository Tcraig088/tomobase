from tomobase.log import logger
import os
import importlib
import inspect
from collections.abc import Iterable

class Item(object):
    def __init__(self, value, name):
        self._value = value    
        self._name = name
      
    def __call__(self, *args, **kwargs):
        if callable(self._value):
            return self._value(*args, **kwargs)
        else:
            logger.warning(f"Item {self._name} is not callable")

    
    @property
    def value(self):
        return self._value
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        self._name = value
        
    @value.setter
    def value(self, value):
        self._index = value


class ItemDict():
    """ A Dictionary like class used to store the available items in the library. Has convenience functions for registering items as part of a plugin system.
    """
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(ItemDict, cls).__new__(cls)
        return cls._instances[cls]
            
    def __init__(self, **kwargs):
        self._index = 0
        self._dict = {}
        self._item_class = Item
        
        #Default Values for using the plugins system
        self._module = 'tomobase'
        self._folder = 'plugins'    
        self._hook = 'default'

        for key, value in kwargs.items():
            newkey = key.upper()
            newkey = newkey.replace(' ', '_')
            self._dict[newkey] = Item(value, key)
            self._index += 1
            
    def __setattr__(self, key, value):
        if key in ['_index', '_dict']:
            super().__setattr__(key, value)
        else:
            self._dict[key] = value

    def __getattr__(self, key):
        try:
            return self._dict[key]
        except KeyError:
            logger.warning(f" object has no attribute '{key}'")
        
    def __getitem__(self, key):
        return self._dict[key]
    
    def __setitem__(self, key, value):
        if key in self._dict:
            logger.warning(f"Key {key} already exists in the dictionary")
        else:
            if value is None:
                value = self._index
            newkey = key.upper()
            newkey = newkey.replace(' ', '_')
            self._dict[newkey] = self._item_class(value, key)
            self._index += 1
        
    def __len__(self):
        return self._index
    
    def loc(self, index):
        for key, item in self._dict.items():
            if item.value == index:
                return self._dict[key]
        logger.warning(f"Index {index} not found in the dictionary")
        
    def items(self):
        return self._dict.items()
    
    def key(self, index):
        for key, item in self._dict.items():
            if item.value == index:
                return key
        logger.warning(f"Index {index} not found in the dictionary")
        
    def append(self, **kwargs):
        for key, value in kwargs.items():
            self[key] = value
                
    def help(self):
        for key, item in self._dict.items():
            logger.info(f"{item.name}: {item.value}")
            logger.info(item.value.__doc__)
            
    def update(self):
        logger.info(f"Updating {self}")
        logger.info(f"Updating {self._module} {self._folder}")
        
        spec = importlib.util.find_spec(self._module)
        if spec is None or spec.origin is None:
            raise ImportError(f"Cannot find the {self._module} package")

        path = os.path.dirname(spec.origin)
        tiltscheme_path = os.path.join(path, self._folder)

        for root, _, files in os.walk(tiltscheme_path):
            for filename in files:
                if filename.endswith('.py'):
                    module_path = os.path.relpath(os.path.join(root, filename), start=path)
                    module_name = self._module+'.'+ module_path.replace(os.sep, '.')[:-3]
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        logger.info(f"Checking {name}, {obj}")
                        if hasattr(obj, self._hook):
                            self._update_item(obj)
                            
    def _update_item(self, obj):
        self._dict[obj.tomobase_name] = obj





 