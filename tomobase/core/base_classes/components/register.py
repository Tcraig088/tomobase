from typing import TypeVar, Generic, Callable, Type, Any
from collections.abc import MutableMapping
import inspect
from functools import wraps


import inspect


from blinker import Signal
import copy

from colorama import Fore, Style, init

init(autoreset=True)


from ...log import logger

K = TypeVar("K")
V = TypeVar("V")



def _safe_name( name: str, islower: bool = True) -> str:
    """_summary_

    Args:
        obj (_type_): _description_
        name (str): _description_
        islower (bool, optional): _description_. Defaults to True.

    Returns:
        str: _description_
    """
    name = name.strip().replace(" ", "_")
    if islower:
        name = name.lower()
    return name

class Node:
    """A node in a registry hierarchy."""

    def __init__(
        self,
        name: str,
        code: int | None = None,
        parent: "Node | None" = None,
    ):
        self.name = name
        self.attr_name = _safe_name(name)
        self.code = code
        self.parent = parent
        self.children: dict[str, Node] = {}
        self.items: dict[str, Any] = {}

    def add_child(self, name: str, code: int | None = None) -> "Node":
        attr = _safe_name(name)
        if hasattr(self, attr):
            raise AttributeError(
                f"Cannot add child {name!r}; attribute {attr!r} already exists"
            )

        node = Node(name=name, code=code, parent=self)
        self.children[name] = node
        setattr(self, attr, node)
        return node

    def add_item(self, name: str, obj: Any) -> Any:
        attr = _safe_name(name, islower=False)
        if hasattr(self, attr):
            raise AttributeError(
                f"Cannot add item {name!r}; attribute {attr!r} already exists"
            )

        self.items[name] = obj
        setattr(self, attr, obj)
        return obj
    
class RegistryBase(MutableMapping, Generic[K, V]):
    """ 
    A registry that supports storing key-value pairs with ease of use functions including, initialization, signals, help functions, and hierarchical registration.
    """
    def __init__(self, key_type: Type[Any], value_type: Type[Any], parent=None):
        self._data: dict[K, V] = {}
        self._key_type = key_type
        self._value_type = value_type
        self._help = self._help_default
        self._parent = parent

        self.added = Signal()
        self.removed = Signal()
        self.renamed = Signal()
        self.updated = Signal()
        
    def register(self, name: str | None = None, category: int | None = None, **kwargs):
        def decorator(obj):
            if name is None:
                obj._tomobase_name = copy.deepcopy(obj.__name__).replace("_", " ")
            else:
                obj._tomobase_name = name

            obj._tomobase_kwargs = kwargs
            obj._tomobase_category = category

            if hasattr(obj, "__name__"):
                key = obj.__name__
                
            else:
                key = obj._tomobase_name
            obj._tomobase_key = key
            self[key] = obj

            return obj

        return decorator
    
    
    def rename(self, old_key: K, new_key: K) -> None:
        if old_key not in self._data:
            raise KeyError(f"Key {old_key} not found")
        if new_key in self._data:
            raise KeyError(f"Key {new_key} already exists")

        value = self._data.pop(old_key)
        self._data[new_key] = value
        self.renamed.send(self, old_key=old_key, new_key=new_key, value=value)

    def help(self) -> str:
        return self._help()

    def set_help(self, help_func: Callable[[], None]):
        self._help = lambda: help_func(self)

    def _help_default(self):
        msg = f"{Fore.GREEN}{self.__class__.__name__}{Style.RESET_ALL}\n"
        for key, value in self._data.items():
            msg += f"{Fore.BLUE}{key}{Style.RESET_ALL}: {value}\n"
        logger.info(msg)
        return msg

    def __str__(self):
        msg = f"{self.__class__.__name__} with {len(self)} items"
        msg += f": {list(self._data.keys())}"
        msg += self._parent.__str__() if self._parent else ""
        return msg
    
    def __getitem__(self, key):
        if key in self._data:
            return self._data[key]
        elif self._parent is not None:
            return self._parent[key]
        raise KeyError(f"Key {key!r} not found")
    
    def __setitem__(self, key, value):
        if not isinstance(key, self._key_type):
            raise TypeError(f"Key must be {self._key_type}, got {type(key)}")

        if inspect.isclass(value):
            try:
                is_sub = issubclass(value, self._value_type)
            except Exception:
                is_sub = False
            if not is_sub:
                raise TypeError(f"Value must be subclass of {self._value_type}, got {type(value)}")
        else:
            if not isinstance(value, self._value_type):
                raise TypeError(f"Value must be {self._value_type}, got {type(value)}")

        if key in self._data:
            old = self._data[key]
            self._data[key] = value
            self.updated.send(self, key=key, old_value=old, new_value=value)
        else:
            self._data[key] = value
            self.added.send(self, key=key, value=value)
            
    def __delitem__(self, key):
        old = self._data.pop(key)
        self.removed.send(self, key=key, old_value=old)
        
    def __iter__(self):
        seen = set()

        # local first (so they override parent)
        for key in self._data:
            seen.add(key)
            yield key

        # then parent
        if self._parent is not None:
            for key in self._parent:
                if key not in seen:
                    yield key
                    
    def __contains__(self, key):
        return key in self._data or (
            self._parent is not None and key in self._parent)
        
    def __len__(self):
        return sum(1 for _ in self)