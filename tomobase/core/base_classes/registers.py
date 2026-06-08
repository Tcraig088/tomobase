from typing import TypeVar, Generic, Callable, Type, Any
from collections.abc import MutableMapping
import inspect
from functools import wraps

from blinker import Signal
import copy

from colorama import Fore, Style, init

init(autoreset=True)

from ..log import logger

K = TypeVar("K")
V = TypeVar("V")

class Registry(MutableMapping, Generic[K, V]):
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

    def register(self, **kwargs):
        def decorator(obj):
            name = kwargs.pop("name", None)
            if name is None:
                obj.tomobase_name = copy.deepcopy(obj.__name__).replace("_", " ").title()
            else:
                obj.tomobase_name = name

            obj._tomobase_kwargs = kwargs
            self[obj.tomobase_name] = obj
            
            if isinstance(obj, type):
                return obj
            
            @wraps(obj)
            def thunk(*args, **kwargs):
                current = self[obj.tomobase_name]
                return current(*args, **kwargs)
            
            return thunk

        return decorator
    
    def __getattr__(self, key):
        key_attr = key.replace("_", " ")
        if key_attr in self._data:
            return self._data[key_attr]
        elif self._parent is not None:
            if key_attr in self._parent:
                return self._parent[key_attr]
        else:
            raise AttributeError(f"{self.__class__.__name__!s} has no attribute {key!r}") from None
             
    def __getitem__(self, key: K) -> V:
        if key in self._data:
            return self._data[key]
        elif self._parent is not None:
            return self._parent[key]
        raise KeyError(f"Key {key!r} not found")

    def __setitem__(self, key: K, value: V) -> None:
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

    def __delitem__(self, key: K) -> None:
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
            self._parent is not None and key in self._parent
        )
    def __len__(self):
        return sum(1 for _ in self)

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
    
    
class HierarchicalRegistry(Registry):
    """ A class that encodes hierarchical information as integer codes, where each level of the hierarchy is represented by a byte.
    
    Example usage:
    ```python
    hr = HierarchicalRegistry(str, int)
    hr.add_hierarchy("A", value=1)  # top-level A -> 0x01000000
    hr.add_hierarchy("B", value=2, parent="A")  # B -> 0x01020000 (inherits A's code and adds 2 in next byte)
    hr.add_hierarchy("C", value=3, parent="B")  # C -> 0x01020300 (inherits A and B's code, adds 3 in next byte)
    ```
    """
    def __init__(self, key_type: Type[Any], value_type: Type[Any]):
        super().__init__(key_type, value_type)
        self._shift = 8
        self._levels = 5
        self._nibble = (1 << self._shift) - 1  # 0xFF
        
    def __setitem__(self, key, value):
        raise NotImplementedError("Use add_hierarchy to add items to HierarchicalRegistry")
        
    def __delitem__(self, key):
        raise NotImplementedError("Cannot delete items from HierarchicalRegistry")
    
    
    def _first_zero_byte_shift(self, code: int) -> int | None:
        """Return shift amount for first zero byte from MSB side, or None if full."""
        for i in range(self._levels):
            shift = (self._levels - 1 - i) * self._shift
            byte = (code >> shift) & self._nibble
            if byte == 0:
                return shift
        return None
    
    def add_hierarchy(self, name: str, value: int = 0, parent: str | None = None) -> int:
        # validate
        if not (1 <= value <= self._nibble):
            raise ValueError(f"Value must be 1..{self._nibble} (got {value})")

        if name in self._data:
            raise KeyError(f"Hierarchy name '{name}' already exists")

        if parent is None:
            # top-level: place in highest byte
            target_shift = (self._levels - 1) * self._shift
            new_code = (value & self._nibble) << target_shift
        else:
            if parent not in self._data:
                raise KeyError(f"Inherit hierarchy '{parent}' not found")
            inherited_index = int(self[parent])
            target_shift = self._first_zero_byte_shift(inherited_index)
            if target_shift is None:
                raise ValueError(f"Inherit hierarchy '{parent}' has no remaining sub-levels")
            new_code = inherited_index | ((value & self._nibble) << target_shift)


        # ensure code not already present
        if any(code == new_code for code in self._data.values()):
            raise ValueError(f"Resulting code {hex(new_code)} already exists in register")

        self._data[name] = int(new_code)
        self.added.send(self, key=name, value=int(new_code))
        logger.debug(f"Added hierarchy '{name}' -> {hex(new_code)} (parent={parent})")
        return int(new_code)
        
    def get_parent(self, category: str|int = 0) -> tuple[str | None, int | None]:
        if isinstance(category, str):
            if category not in self._data:
                raise KeyError(f"Hierarchy '{category}' not found")
            else:
                category = self._data[category]
        
        parts = []
        for i in range(self._levels):
            s = (self._levels - 1 - i) * self._shift
            parts.append((category >> s) & self._nibble)
        while parts and parts[-1] == 0:
            parts.pop()

        # top-level (no parent)
        if not parts or len(parts) == 1:
            return (None, None)

        # clear the last non-zero part to get the parent code
        last_idx = len(parts) - 1
        clear_shift = (self._levels - 1 - last_idx) * self._shift
        parent_code = category & ~(self._nibble << clear_shift)

        # find registered key for parent_code if present
        parent_name = next((k for k, v in self._data.items() if int(v) == parent_code), None)
        if parent_name is None:
            return (None, None)
        return (parent_name, parent_code)

    def get_key(self, code: int) -> str | None:
        for key, val in self._data.items():
            if val == code:
                return key
            
    def help_categories(self):
        # list sorted by code
        _dict = self
        items = sorted(_dict._data.items(), key=lambda kv: int(kv[1]))

        shift = getattr(_dict, "_shift", 8)
        levels = getattr(_dict, "_levels", 5)
        mask = (1 << shift) - 1

        def split_levels(code: int):
            parts = []
            for i in range(levels):
                s = (levels - 1 - i) * shift
                parts.append((code >> s) & mask)
            while parts and parts[-1] == 0:
                parts.pop()
            return parts

        rows = []
        for name, val in items:
            code = int(val)
            parts = split_levels(code)
            parts_str = ".".join(f"{p:02X}" for p in parts) if parts else "00"
            rows.append((name, f"0x{code:0{levels*2}X}", parts_str))

        # compute column widths and render
        name_w = max(len("Name"), max(len(r[0]) for r in rows))
        code_w = max(len("Code"), max(len(r[1]) for r in rows))
        lvl_w  = max(len("Levels"), max(len(r[2]) for r in rows))
        hdr = f"{'Name':{name_w}}  {'Code':{code_w}}  {'Levels':{lvl_w}}"
        sep = "-" * (name_w + code_w + lvl_w + 4)
        lines = [hdr, sep] + [f"{n:{name_w}}  {c:{code_w}}  {l:{lvl_w}}" for n, c, l in rows]
        logger.info("\n" + "\n".join(lines))