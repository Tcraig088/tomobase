import sys

from tomobase.core import logger
from .backends import qt

logger.debug("Importing Tomobase Plugins [Qt Backend]")

parent_pkg = sys.modules[__package__]
parent_pkg.qt = qt
sys.modules[f"{__package__}.qt"] = qt
