import importlib

from . import packages, registers
from .log import logger

_initialized = False

def get_backend_compatibility(pkg_name):
    compatibility = []
    if module_exists(f"{pkg_name}.core.plugins"):
        compatibility.append("agnostic")
    if module_exists(f"{pkg_name}.core.qt_plugins"):
        compatibility.append("qt")
    if module_exists(f"{pkg_name}.core.jupyter_plugins"):
        compatibility.append("jupyter")
    return compatibility

def module_exists(module_name):
    return importlib.util.find_spec(module_name) is not None

def bootstrap(qt_enabled = False, jupyter_enabled = False):
    global _initialized
    if _initialized:
        return
    _initialized = True

    for pkg in packages.get_packages():
        compatibility = get_backend_compatibility(pkg)
        if not compatibility:
            logger.warning(f"Package '{pkg}' does not have any compatible backends. Skipping.")
            continue
        if 'agnostic' in compatibility:
            importlib.import_module(f"{pkg}.core.plugins")
        if qt_enabled and 'qt' in compatibility:
            importlib.import_module(f"{pkg}.core.qt_plugins")
        if jupyter_enabled and 'jupyter' in compatibility:
            importlib.import_module(f"{pkg}.core.jupyter_plugins")

    from .bootstraps import bootstrap_process
    for key, value in list(registers.processes.items()):
        registers.processes[key] = bootstrap_process(value)
