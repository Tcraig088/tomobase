import sys

from .core import data_classes, logger, progress
from .domain import phantoms, procedures

logger.debug("Importing Tomobase Plugins [Backend Agnostic]")

# Get the parent package module object, i.e. the `tomobase` module itself
parent_pkg = sys.modules[__package__]

# Expose these as attributes on `tomobase`
parent_pkg.phantoms = phantoms
parent_pkg.procedures = procedures

# Expose these as real importable module aliases
sys.modules[f"{__package__}.phantoms"] = phantoms
sys.modules[f"{__package__}.procedures"] = procedures
