
import enum
import logging
from tomobase.log import logger

class GPUContext(enum.Enum):
    CUPY = 1
    NUMPY = 2


class EnvironmentRegistration():
    """
    Singleton class to check if submodules are available or not.

    Attributes:
    tomobase (bool): True if tomobase is available, False otherwise.
    tomoacquire (bool): True if tomoacquire is available, False otherwise.
    
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EnvironmentRegistration, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self._hyperspy_checked = False
        self._hyperspy_available = False

        self._cupy_checked = False
        self._cupy_available = False

    @property
    def hyperspy(self):
        if not self._hyperspy_checked:
            try:
                import hyperspy.api as hs
                self._hyperspy_available = True
            except ModuleNotFoundError:
                self._hyperspy_available = False
                logger.error("hyperspy module not found.")
            except Exception as e:
                self._hyperspy_available = False
                logger.error(e)
        self._hyperspy_checked = True
        return self._hyperspy_available
    
    @property
    def cupy(self):
        if not self._cupy_checked:
            try:
                import cupy as cp
                self._cupy_available = True
            except ModuleNotFoundError:
                self._cupy_available = False
                logging.error("cupy module not found.")
            except Exception as e:
                self._cupy_available = False
                logging.error(e)
        self._cupy_checked = True
        return self._cupy_available
    


import numpy as xp
TOMOBASE_ENVIRONMENT = EnvironmentRegistration()
