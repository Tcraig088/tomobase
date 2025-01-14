from tomobase.log import logger

class TransformItem():
    """
    Represents an  available datatype in the library.
    
    Attributes:
        index (int): The index of the data type in the library
        widget (QWidget): The widget that is associated with the data type
        
    Methods:    
        value(): Returns the index of the data type
        
    """
    def __init__(self, index, widget=None):
        super().__init__()
        self._index = index
        self._widget = widget
        self._categories = {}
    
    @property
    def index(self):
        return self._index
    
    @property
    def widget(self):
        return self._widget
    
    @property
    def categories(self):
        return self._categories
    
    def value(self):
        """
        Returns the index of the datatype.
        
        Returns:
            _index (int): returns class index
        """
        return self._index
    
    def append(self, hierarchy):
        """
        Adds a named data type to the library, maintaining the hierarchy.
        
        Arguments:
            hierarchy (dict): The hierarchical dictionary to add.
        """
        self._add_to_hierarchy(self._categories, hierarchy)

    def _add_to_hierarchy(self, current_dict, hierarchy):
        """
        Recursively adds items to the hierarchy.
        
        Arguments:
            current_dict (dict): The current level of the dictionary.
            hierarchy (dict): The hierarchical dictionary to add.
        """
        for key, value in hierarchy.items():
            if key not in current_dict:
                current_dict[key] = {}
            if isinstance(value, dict):
                self._add_to_hierarchy(current_dict[key], value)
            else:
                if isinstance(current_dict[key], list):
                    if value not in current_dict[key]:
                        current_dict[key].append(value)
                else:
                    current_dict[key] = [value]
    

class TransformItemDict():
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
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(TransformItemDict, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, **kwargs):
        self._items = int(0)
        self._dict = {}
        for key, value in kwargs.items():
            self._dict[key] = TransformItem(self._items, value)
            self._items += 1
            
    def __setattr__(self, key, value):
        if key in ['_items', '_dict']:
            super().__setattr__(key, value)
        else:
            self._dict[key] = TransformItem(self._items, value)
            self._items += 1

    def __getattr__(self, key):
        try:
            return self._dict[key]
        except KeyError:
            raise AttributeError(f"'DataItemDict' object has no attribute '{key}'")

    def __getitem__(self, key):
        return self._dict[key]
    
    def append(self, **kwargs):
        """
        Adds a named data type to the library if it is not already present. Example TPMPBASE_DATATYPES.append(NEWDATA = NewDataWidget). will add a new datatype named NEWDATA to the library and will registed a widget for inspecting that datatype napari.
        
        Args:
            **kwargs: A dictionary of named data types to add to the library
        """
        for key, value in kwargs.items():
            if key in self._dict:
                logger.warning(f"Data Type '{key}' has already been registered in the library.")
            else:
                self._dict[key] = TransformItem(self._items, value)
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
            if item.index == index:
                return self._dict[key]
        raise Exception(f"Index {index} not found in TOMOBASE_DATATYPES")
    
    def items(self):
        """
        Returns an iterator over the (key, value) pairs in the dictionary.
        
        Returns:
            iterator: an iterator over the (key, value) pairs in the dictionary
        """
        return self._dict.items()
    
    def key(self, index):
        """
        Returns the key of the datatype at the specified index.
        
        Args:
            index (int): The index of the datatype to return

        Returns:
            str: the key of the datatype at the specified index
        """
        for key, item in self._dict.items():
            if item.index == index:
                return key
            
        raise Exception(f"Index {index} not found in TOMOBASE_DATATYPES")
    
TOMOBASE_TRANSFORM_CATEGORIES = TransformItemDict( ALIGN=None, 
                                         PROJECT=None,
                                         RECONSTRUCT=None)