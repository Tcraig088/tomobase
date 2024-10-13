from tomobase.log import logger
from tomobase.napari.layer_widgets.sinogram import SinogramDataWidget
from tomobase.napari.layer_widgets.image import ImageDataWidget
from tomobase.napari.layer_widgets.volume import VolumeDataWidget

class DataTypeItem():
    """
    Represents an  available datatype in the library.
    
    Attributes:
        index (int): The index of the data type in the library
        widget (QWidget): The widget that is associated with the data type
        
    Methods:    
        value(): Returns the index of the data type
        
    """
    def __init__(self, index, widget):
        self._index = index
        self._widget = widget
        
    @property
    def index(self):
        return self._index
    
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


class DataItemDict():
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
            cls._instance = super(DataItemDict, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, **kwargs):
        self._items = int(0)
        self._dict = {}
        for key, value in kwargs.items():
            self._dict[key] = DataTypeItem(self._items, value)
            self._items += 1
            
    def __setattr__(self, key, value):
        if key in ['_items', '_dict']:
            super().__setattr__(key, value)
        else:
            self._dict[key] = DataTypeItem(self._items, value)
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
                self._dict[key] = DataTypeItem(self._items, value)
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
         
TOMOBASE_DATATYPES = DataItemDict( IMAGE=ImageDataWidget, SINOGRAM=SinogramDataWidget, VOLUME=VolumeDataWidget)