import types
import inspect
from copy import deepcopy
from tomobase.log import logger

def tomobase_hook_tiltscheme(name: str):
    """a decorator used to mark a class as a tiltscheme. The class is either a standard class used to define the tiltscheme or a QWidget used to attach to napari. 
    see the plugins tutorial for more information on how to use this decorator. returns a decorated class

    Args:
        name (str): the name of the tilt scheme. Should be readable casing and spaces. 
    """
    def decorator(cls):
        cls.tomobase_name = name
        cls.is_tomobase_tiltscheme = True
        return cls
    return decorator

def tomobase_hook_process(**kwargs):
    """A decorator used to mark a function or class as a tomography process. The function or class is either a standard function or class used to define the process or a QWidget used to attach to napari.
    
    Args:
        name (str): the name of the process. Should be readable casing and spaces.
        category (enum.TransformCategory or List[enum.TransformCategory]): the category of the process. Should be a member of the TransformCategories enum.
        includes (list[enum.DataModules]): a list of data types that the process can handle. Either Numpy Cupy or Torch.
        excludes (list[enum.DataModules]): a list of strings that define the data types that the process cannot handle. Cannot define both includes and excludes
        subcategories (dict(enum.TransformCategory,[list[str]])): a list of strings that define the subcategories of the process. Used when adding the process to the napari menu.
    """
    def decorator(obj):
        if isinstance(obj, types.FunctionType):
            return _process_function_decorator(obj, **kwargs)
        elif inspect.isclass(obj):
            return _process_class_decorator(obj, **kwargs)
        else:
            raise TypeError("Unsupported category")
    return decorator

def _process_function_decorator(func, **kwargs):
    name = kwargs.get("name", None)
    if name is None:
        raise ValueError("Name is required")
    category = kwargs.get("category", None)
    if category is None:
        raise ValueError("category is required")
    includes = kwargs.get("includes", None)
    excludes = kwargs.get("excludes", None)
    subcategories = deepcopy(kwargs.get("subcategories", {}))

    subcategory_added = False
    if isinstance(category, list):
        for item in category:
            if item not in subcategories:
                subcategories[item] = name
                subcategory_added = True
    elif category not in subcategories:
            subcategories[category] = name
            subcategory_added = True
    
    if not subcategory_added:
        subcategories = add_name_to_dict(subcategories, name)

    func.tomobase_name = name
    func.tomobase_category = category
    func.is_tomobase_process = True
    func.tomobase_includes = includes
    func.tomobase_excludes = excludes
    func.tomobase_subcategories = subcategories
    return func



def _process_class_decorator(cls, **kwargs):
    name = kwargs.get("name", None)
    if name is None:
        raise ValueError("Name is required")
    category = kwargs.get("category", None)
    if category is None:
        raise ValueError("Category is required")
    includes = kwargs.get("includes", None)
    excludes = kwargs.get("excludes", None)
    subcategories = kwargs.get("subcategories", {})
    
    if isinstance(category, list):
        for item in category:
            if item not in subcategories:
                subcategories[item] = name
    else:
        if category not in subcategories:
            subcategories[category] = name
            
    subcategories = add_name_to_dict(subcategories, name)
        
    
    
    cls.tomobase_name = name
    cls.tomobase_category = category
    cls.is_tomobase_process = True
    cls.tomobase_includes = includes
    cls.tomobase_excludes = excludes
    cls.tomobase_subcategories = subcategories

    return cls

def add_name_to_dict(d, name):
    """
    Recursively replace bottom string values in a dictionary of dictionaries with a dictionary containing that string value.
    
    Arguments:
        d (dict): The dictionary to process.
    
    Returns:
        dict: The processed dictionary with bottom string values replaced.
    """
    for key, value in d.items():
        if isinstance(value, dict):
            d[key] = add_name_to_dict(value, name)
        elif isinstance(value, str):
            d[key] = {value: name}
    return d
