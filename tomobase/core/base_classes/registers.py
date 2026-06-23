from typing import TypeVar, Generic, Callable, Type, Any
from collections.abc import MutableMapping
import inspect
from functools import wraps

from blinker import Signal
import copy

from colorama import Fore, Style, init

from .components.register import RegistryBase, Node, _safe_name

init(autoreset=True)

from ..log import logger


class HierarchicalRegistry(RegistryBase):
    """ A class that encodes hierarchical information as integer codes, where each level of the hierarchy is represented by a byte.

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
    
    def get_tree(self, code: int) -> list:
        """ Returns a list of the parent keys for the individual hierarchies in the registry"""
        tree = [self.get_key(code)]
        parent_name, parent_code = self.get_parent(code)
        while parent_name is not None:
            tree.append(parent_name)
            parent_name, parent_code = self.get_parent(parent_code)
            
        tree = tree[::-1]
        return tree

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
        
        
class Registry(RegistryBase):
    """ 
    A registry that supports storing key-value pairs with ease of use functions including, initialization, signals, help functions, and hierarchical registration.
    """
    def __init__(self, key_type: Type[Any], value_type: Type[Any], parent=None):
        super().__init__(key_type, value_type, parent)
        self._hierarchy = None  
        self._initialized = False

    def register(self, name: str | None = None, category: int | None = None, **kwargs):
        base_decorator = super().register(name=name, category=category, **kwargs)

        def decorator(obj):
            registered_obj = base_decorator(obj)
            actual_name = obj._tomobase_key

            if self._hierarchy is not None and category is not None:
                node = self._get_node(category)
                node.add_item(name=actual_name, obj=registered_obj)
            else: 
                setattr(self, actual_name, registered_obj)
            
            
            if self._initialized:
                self._initialize_item(actual_name, self._data[actual_name])
            return registered_obj

        return decorator
    
    
    def set_initialization_function(self, func):
        """ Sets the initialization function for the registry. This function will be called on each registered item when the registry is initialized.
        
        Args:
            func (Callable): A function that takes a registered item and returns an initialized version of it.
        """
        self.initialization_function = func
        
    def initialize(self):
        """ Initializes all registered items in the registry using the initialization function. This is typically called after all items have been registered.
        """
        if not hasattr(self, 'initialization_function'):
            raise AttributeError("Initialization function not set. Use set_inizialization_function to set it.")
        
        for key in self._data:
            self._initialize_item(key, self._data[key])
            
        self._initialized = True
        
        
    def _initialize_item(self, key, value):
        
        func = copy.deepcopy(value)
        category = func._tomobase_category if hasattr(func, "_tomobase_category") else None
        self._data[key] = self.initialization_function(value)
        
        if self._hierarchy is not None:
            node = self._get_node(category)
            setattr(node, _safe_name(key, islower=False), self._data[key])
        else:
            setattr(self, _safe_name(key, islower=False), self._data[key])
        
    def _set_node(self, key:str, code:int|None):
        """ Adds an attribute to the registry using the key code of a hierarchy
        Args:
            key (str): The name of the hierarchy to set as an attribute.
            code (int | None): The code of the hierarchy to set as an attribute.
        """
        
        
        tree = self.hierarchy.get_tree(code)
        node = self
        excluded = self.hierarchy.get_key(self._exclude_code)
        for part in tree:
            if part == excluded:
                pass
            else:
                if not hasattr(node, _safe_name(part)):
                    if node is not Node:
                        setattr(node, _safe_name(part, islower=True), Node(name=part, code=code, parent=node))
                    else: 
                        node.add_child(name=_safe_name(part, islower=True), code=code)
                node = getattr(node, _safe_name(part))
       
    def _get_node(self, code:int) -> Node:
        """ Gets a node from the registry hierarchy.
        
        Args:
            code (int): The code of the hierarchy to get.
        """
        tree = self.hierarchy.get_tree(code)
        node = self
        excluded = self.hierarchy.get_key(self._exclude_code)
        for part in tree:
            if part == excluded:
                continue
            else:
                node = getattr(node, _safe_name(part), None)
                if node is None:
                    raise ValueError(f"Node not found for hierarchy code {code} ")  
        return node
    
    def _remove_node(self, key:str):
        """ Removes a node from the registry hierarchy.
        
        Args:
            key (str): The name of the hierarchy to remove.
        """
        node = getattr(self, _safe_name(key), None)
        if node is not None:
            parent_node = node.parent
            if parent_node is not None:
                del parent_node.children[key]
                delattr(parent_node, _safe_name(key))
            else:
                delattr(self, _safe_name(key))
    
    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if self._initialized:
            self._data[key] = self.initialization_function(self._data[key])
        
            
    @property
    def hierarchy(self) -> HierarchicalRegistry | None:
        return self._hierarchy
    

    def set_hierarchy(self, hierarchy: HierarchicalRegistry, code:int):
        if not isinstance(hierarchy, HierarchicalRegistry):
            raise TypeError("Hierarchy must be a HierarchicalRegistry")
        if self._hierarchy is not None:
            raise ValueError("Hierarchy has already been set and cannot be changed")
        if code not in hierarchy._data.values():
            raise ValueError("Code must be a valid hierarchy code in the provided hierarchy")
        
        self._hierarchy = hierarchy
        self._exclude_code = code
        items = sorted(self.hierarchy._data.items(), key=lambda kv: int(kv[1]))
        for key, value in items:
            self._set_node(key, value)
            
        self.hierarchy.added.connect(self._on_hierarchy_added)
        self.hierarchy.removed.connect(self._on_hierarchy_removed)
        
    def _on_hierarchy_added(self, sender, key, value):
        self._set_node(key, value)

    def _on_hierarchy_removed(self, sender, key, old_value):
        self._remove_node(key)