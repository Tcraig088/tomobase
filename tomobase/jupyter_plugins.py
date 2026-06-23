import sys

from tomobase.core.log import logger, tomobase_logger
from .backends import jupyter

logger.debug("Importing Tomobase Plugins [Jupyter Backend]")

parent_pkg = sys.modules[__package__]
parent_pkg.jupyter = jupyter
sys.modules[f"{__package__}.jupyter"] = jupyter
tomobase_logger.disable_cli()
