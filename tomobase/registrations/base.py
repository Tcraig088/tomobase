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
            logger.warning(f"Item {self._name} is not callable!")

    def __setitem__(self, name, value):
        if isinstance(self._value, dict) or isinstance(self._value, ItemDictNonSingleton):
            self._value[name] = value
        else:
            super().__setattr__(name, value)
            
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
        self._value = value

    def items(self):
        if isinstance(self._value, dict) or isinstance(self._value, ItemDictNonSingleton) or isinstance(self._value, ItemDict):
            return self._value.items()
        else:
            _dict = {}
            msg = f"Item {self._name} is not a dictionary. Cannot return items.\n"
            msg += f"Item {self._name} is of type {type(self._value)}"
            logger.warning(msg)
            return _dict.items()

class ItemDictNonSingleton():      
    def __init__(self, **kwargs):
        
        # Note For Developers check setattr otherwise youll include your variables as dict keys and this will mess the whole dict up
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
            if value is None:
                value = self._index
            self._dict[newkey] = self._item_class(value, key)
            self._index += 1
            
    def __setattr__(self, key, value):
        if key in ['_index', '_dict', '_module', '_folder', '_hook', '_item_class']:
            # Allow these keys to be set as attributes
            super().__setattr__(key, value)
        else:
            # Add other keys to the internal dictionary
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
            pass
        else:
            logger.debug(f"Adding {key} to the dictionary")
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
            logger.info(f"{key}: {item.name}, {item.value}")

            
    def update(self):
        #logger.warning(f"Updating modlules {self }")
        #logger.info(f"Module {self}: {self._module} {self._folder}")
        
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
                    for name, obj in inspect.getmembers(module):
                        if inspect.isclass(obj) or inspect.isfunction(obj):
                            if hasattr(obj, self._hook):
                                #logger.info(f"Found {self._hook} in {name}")
                                self._update_item(obj)
                            
    def _update_item(self, obj):
        self[obj.tomobase_name] = obj


class ItemDict(ItemDictNonSingleton):
    _instances = {}

    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(ItemDict, cls).__new__(cls)
        return cls._instances[cls]
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)




