import importlib
from .registers import packages

_initialized = False

def bootstrap():
    global _initialized
    if _initialized:
        return
    _initialized = True

    for pkg in packages.get_packages():
        importlib.import_module(f"{pkg}.plugins")