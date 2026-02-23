from typing import List, TypeVar, Generic, Callable, Type, Any
from collections.abc import MutableMapping
from qtpy.QtCore import QObject, Signal
import importlib
import inspect
import os
from functools import partial


from colorama import Fore, Style, init
init(autoreset=True)

from ..log import logger
from .packages import get_paths, get_packages, load_packages_from_files

K = TypeVar("K")
V = TypeVar("V")

# Combine QObject's metaclass and MutableMapping's metaclass to avoid
# "metaclass conflict" when inheriting both QObject and an ABC.
try:
    RegistryMeta = type("RegistryMeta", (type(QObject), type(MutableMapping)), {})
except TypeError:
    # Fallback: if combining metaclasses fails, use a simple type
    RegistryMeta = type

class Registry(QObject, MutableMapping, Generic[K, V], metaclass=RegistryMeta):
    added = Signal(object, object)      # key, value
    removed = Signal(object, object)    # key, old_value
    renamed = Signal(object, object, object)  # key, old, new
    updated = Signal()    # key, value

    def __init__(self, key_type: Type[Any], value_type: Type[Any], parent=None):
        super().__init__(parent)
        self._data: dict[K, V] = {}
        self._key_type = key_type
        self._value_type = value_type
        self._hook = None
        self._init = False
        
        self._help = self._help_default
        
    def __getitem__(self, key: K) -> V:
        return self._data[key]

    def __setitem__(self, key: K, value: V) -> None:
        if not isinstance(key, self._key_type):
            raise TypeError(f"Key must be {self._key_type}, got {type(key)}")
        # Allow either an instance of the expected value type or a class
        # that subclasses the expected value type. Some Qt-wrapped classes
        # appear as SIP wrapper types, so we check for class-ness and use
        # a safe issubclass check when appropriate.
        import inspect as _inspect

        if _inspect.isclass(value):
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
            self.renamed.emit(key, old, value)
        else:
            self._data[key] = value
            self.added.emit(key, value)

    def __delitem__(self, key: K) -> None:
        old = self._data.pop(key)
        self.removed.emit(key, old)

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)
    
    def rename(self, old_key: K, new_key: K) -> None:
        if old_key not in self._data:
            raise KeyError(f"Key {old_key} not found")
        if new_key in self._data:
            raise KeyError(f"Key {new_key} already exists")
        value = self._data.pop(old_key)
        self._data[new_key] = value
        self.renamed.emit(new_key, old_key, value)
        
    def update(self, explicit: bool = True):
        if not explicit:
            if self._init:
                logger.debug(f"{Fore.YELLOW}Registry already initialized, skipping implicit update{Style.RESET_ALL}")
                return
        
        self._init = True
        logger.debug(f"{Fore.YELLOW}Updating registry with hook '{self._hook}' (explicit={explicit}){Style.RESET_ALL}")
        packages = load_packages_from_files(get_paths())
        for package in get_packages():
            spec = importlib.util.find_spec(package)
            if spec is None or spec.origin is None:
                logger.warning(f"Cannot find the {package} package")
            else:
                path = os.path.dirname(spec.origin)
                packages.append(path)
        
        for package in packages:
            logger.debug(f"{Fore.BLUE}Scanning {package} for {self._hook} items{Style.RESET_ALL}")     
            for root, directories, files in os.walk(package):
                root_name = root.split(os.path.basename(package))[-1].replace(os.sep, '.').strip('.')
                root_name = os.path.basename(package)
                for file in files:
                    if file.endswith('.py'):
                        package_path = os.path.relpath(os.path.join(root, file), start=package)
                        package_name = root_name + '.' + os.path.splitext(package_path)[0].replace(os.sep, '.')
                        logger.debug(f"Importing {package_name} to check for {self._hook} items")
                        subpackage = importlib.import_module(package_name)
                        
                        for name, obj in inspect.getmembers(subpackage):
                            if inspect.isclass(obj) or inspect.isfunction(obj):
                                if getattr(obj, self._hook, False):
                                    logger.debug(f"Registered {name} from {package_name}")
                                    self[obj.tomobase_name] = obj
                                
                                
    def help(self) -> str:
        self._help()
    
    def set_help(self, help_func: Callable[[], None]):
        self._help = lambda :help_func(self)
        
    def _help_default(self):
        msg = f"{Fore.GREEN}{self.__class__.__name__}{Style.RESET_ALL}\n" 
        for key, value in self._data.items():
            msg += f"{Fore.BLUE}{key}{Style.RESET_ALL}: {value}\n"
        logger.info(msg)


class CategoryRegistry(Registry):
    def __init__(self, key_type: Type[Any], value_type: Type[Any], parent=None):
        super().__init__(key_type, value_type, parent)
        self._shift = 8
        self._levels = 4
        self._nibble = (1 << self._shift) - 1  # 0xFF
        
    def __setitem__(self, key, value):
        raise NotImplementedError("Use add_category to add items to CategoryRegistry")
        
    def __delitem__(self, key):
        raise NotImplementedError("Cannot delete items from CategoryRegistry")
    
    
    def _first_zero_byte_shift(self, code: int) -> int | None:
        """Return shift amount for first zero byte from MSB side, or None if full."""
        for i in range(self._levels):
            shift = (self._levels - 1 - i) * self._shift
            byte = (code >> shift) & self._nibble
            if byte == 0:
                return shift
        return None
    
    def add_category(self, name: str, value: int = 0, inheritor: str | None = None) -> int:
        # validate
        if not (1 <= value <= self._nibble):
            raise ValueError(f"Value must be 1..{self._nibble} (got {value})")

        if name in self._data:
            raise KeyError(f"Category name '{name}' already exists")

        if inheritor is None:
            # top-level: place in highest byte
            target_shift = (self._levels - 1) * self._shift
            new_code = (value & self._nibble) << target_shift
        else:
            if inheritor not in self._data:
                raise KeyError(f"Inherit category '{inheritor}' not found")
            inherited_index = int(self[inheritor])
            target_shift = self._first_zero_byte_shift(inherited_index)
            if target_shift is None:
                raise ValueError(f"Inherit category '{inheritor}' has no remaining sub-levels")
            new_code = inherited_index | ((value & self._nibble) << target_shift)

        # ensure code not already present
        if any(code == new_code for code in self._data.values()):
            raise ValueError(f"Resulting code {hex(new_code)} already exists in register")

        self._data[name] = int(new_code)
        self.added.emit(name, int(new_code))
        logger.debug(f"Added category '{name}' -> {hex(new_code)} (inheritor={inheritor})")
        return int(new_code)
        
    def get_inheritor(self, category: str|int = 0) -> str | None:
        if isinstance(category, str):
            if category not in self._data:
                raise KeyError(f"Category '{category}' not found")
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
            return None
        return (parent_name, parent_code)

    def get_key(self, code: int) -> str | None:
        for key, val in self._data.items():
            if val == code:
                return key