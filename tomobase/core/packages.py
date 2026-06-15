
import importlib
import sys
from typing import List, Union 

import json
import pathlib
import os 

def add_path(path: Union[str, pathlib.Path]) -> None:
    if isinstance(path, pathlib.Path):
        path = str(path)
    
    json_path = os.path.dirname(__file__)
    json_path = os.path.join(json_path, 'packages.json')
    
    _dict = json.load(open(json_path, 'r'))
    _dict['paths'].append(path)
    json.dump(_dict, open(json_path, 'w'), indent=4)
    
def add_package(name: str) -> None:
    """Registers a package with tomobase so that it is searched for registered items and initialized. The package should be imported before calling this function and the package is only added if it is not already in the list of packages. This is useful for packages that are not in the default search path of tomobase or for packages that are not compatible with the default context of tomobase. The package should be imported before calling this function and the package is only added if it is not already in the list of packages. 

    Args:
        name (str): the name of the package to register.
    """
    json_path = os.path.dirname(__file__)
    json_path = os.path.join(json_path, 'packages.json')
    
    _dict = json.load(open(json_path, 'r'))
    if name not in _dict['packages']:
        _dict['packages'].append(name)
    json.dump(_dict, open(json_path, 'w'), indent=4)
    
def get_paths() -> List[str]:
    json_path = os.path.dirname(__file__)
    json_path = os.path.join(json_path, 'packages.json')
    
    _dict = json.load(open(json_path, 'r'))
    return _dict['paths']

def get_packages() -> List[str]:
    json_path = os.path.dirname(__file__)
    json_path = os.path.join(json_path, 'packages.json')
    
    _dict = json.load(open(json_path, 'r'))
    return _dict['packages']


def load_packages_from_files(paths: List[str]):
    packages = []
    for path in paths:
        path = pathlib.Path(path).resolve()
        module_name = path.stem  # "environment"

        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load spec for {path}")

        package = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = package  # important
        spec.loader.exec_module(package)
        packages.append(package)
    return packages

