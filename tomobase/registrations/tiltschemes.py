from tomobase.log import logger
import os
import importlib
import inspect

from qtpy.QtWidgets import QWidget

class TiltSchemeItem():
    """
    Represents an  available datatype in the library.
    
    Attributes:
        index (int): The index of the data type in the library
        widget (QWidget): The widget that is associated with the data type
        
    Methods:    
        value(): Returns the index of the data type
        
    """
    def __init__(self, index, controller=None, widget=None):
        self._index = index
        self._controller = controller
        self._widget = widget
        
    @property
    def index(self):
        return self._index
    
    @property
    def controller(self):
        return self._controller

    @property
    def widget(self):
        return self._widget
    
    def value(self):
        """
        Returns the index of the datatype.
        
        Returns:
            _index (int): returns class index
        """
        return self._index


class TiltSchemeItemDict():
    """
    A Dictionary like class used to store the available data types in the library. Has convenience functions for registering data types. To   
    
    Attributes:
        _items (int): The number of data types in the library
        _dict (dict{str: DataTypeItem}): A dictionary of named data types
        
    Methods:
        append(**kwargs): Adds a named data type to the library
        loc(index): Returns the data type at the specified index
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TiltSchemeItemDict, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._items = int(0)
        self._dict = {}
    
    def __setattr__(self, key, value):
        if key in ['_items', '_dict']:
            super().__setattr__(key, value)
        else:
            self._dict[key] = TiltSchemeItem(self._items, value)
            self._items += 1


    def __getitem__(self, key):
        return self._dict[key]
    
    def update(self):
        """
        Inspects the 'tiltseries' folder in the 'plugins' folder of the 'tomoacquire' package
        and imports all classes that contain a specific attribute.
        """
        # Find the location of the 'tomoacquire' package
        spec = importlib.util.find_spec('tomobase')
        if spec is None or spec.origin is None:
            raise ImportError("Cannot find the 'tomoacquire' package")

        # Construct the path to the 'tiltseries' folder within the 'plugins' folder
        path = os.path.dirname(spec.origin)
        tiltscheme_path = os.path.join(path, 'tiltschemes')
        attribute_name = 'is_tomobase_tiltscheme'
        
        for root, _, files in os.walk(tiltscheme_path):
            for filename in files:
                if filename.endswith('.py'):
                    module_path = os.path.relpath(os.path.join(root, filename), start=path)
                    module_name = 'tomobase.'+ module_path.replace(os.sep, '.')[:-3]
                    module = importlib.import_module(module_name)
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if hasattr(obj, attribute_name):
                            self.append(obj.tomobase_name,obj)
         
        
    def append(self, key, value):
        """
        Adds a named data type to the library if it is not already present. Example TPMPBASE_DATATYPES.append(NEWDATA = NewDataWidget). will add a new datatype named NEWDATA to the library and will registed a widget for inspecting that datatype napari.
        
        Args:
            **kwargs: A dictionary of named data types to add to the library
        """
        if key in self._dict:
            if self._dict[key].widget is None:
                self._dict[key]._widget = value
            elif self._dict[key].controller is None:
                self._dict[key]._controller = value 
            else:
                logger.warning(f"Data Type '{key}' has already been registered in the library.")
        else:
            if isinstance(value, type) and issubclass(value, QWidget):
                self._dict[key] = TiltSchemeItem(self._items, widget=value)
            else:
                self._dict[key] = TiltSchemeItem(self._items, controller=value)
            self._items += 1
                
    def loc(self, index):
        """
        Returns the datatype at the specified index.
        
        Args:
            index (int): The index of the datatype to return

        Returns:
            DataTypeItem: the datatype item at the specified index
        """
        for key, item in self._dict.items():
            if key == index:
                return self._dict[key]
        raise Exception(f"Index {index} not found in TOMOBASE_DATATYPES")

    def items(self):
        """
        Returns an iterator over the (key, value) pairs in the dictionary.
        
        Returns:
            iterator: an iterator over the (key, value) pairs in the dictionary
        """
        return self._dict.items()
  
