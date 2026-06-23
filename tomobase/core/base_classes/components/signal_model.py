
import copy
import random
from functools import partial
from blinker import Signal

from .. import registers
from ... import log

class SignalModel():
    ipywidgets = registers.Registry(str, object)
    
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.ipywidgets = registers.Registry(str, object, parent=cls.ipywidgets)
    
    def __init__(self, data, *args, **kwargs):
        self._init_runtime_state()


    def _init_runtime_state(self):
        self._instance_id = random.getrandbits(32)  
        self.data_refreshed = Signal()
        self.data_appended = Signal()
        self.data_removed = Signal()
        
        self.interactive = registers.Registry(str, object)
        for key, value in self.ipywidgets.items():
            self.interactive.register(name=value._tomobase_name)(partial(value, self))
            
        self.ipywidgets.added.connect(self.added_interactive, weak=False)
        self.ipywidgets.removed.connect(self.remove_interactive, weak=False)
        self.ipywidgets.updated.connect(self.update_interactive, weak=False)
        self.ipywidgets.renamed.connect(self.rename_interactive, weak=False)
        
    def refresh(self):
        """Refresh the data."""
        self.data_refreshed.send(self)

    def append(self, item):
        """Append an item to the data."""
        self.data_appended.send(self, item=item)

    def remove(self, item):
        """Remove an item from the data."""
        self.data_removed.send(self, item=item)
        
    def added_interactive(self, key, value):
        self.interactive[key] = partial(value, self)
        
    def remove_interactive(self, key):
        del self.interactive[key]
        
    def update_interactive(self, key, value):
        self.interactive[key] = partial(value, self)
        
    def rename_interactive(self, old_key, new_key):
        self.interactive.rename(old_key, new_key)
        
    def clone(self, deep=True):
        cls = self.__class__
        new = cls.__new__(cls)

        for key, value in self.__dict__.items():
            if isinstance(value, (Signal, registers.Registry)):
                continue
            setattr(new,key, copy.deepcopy(value) if deep else copy.copy(value))

        new._init_runtime_state()
        self._instance_id = random.getrandbits(32)
        return new

    def __copy__(self):
        return self.clone(deep=False)

    def __deepcopy__(self, memo):
        return self.clone(deep=True)
