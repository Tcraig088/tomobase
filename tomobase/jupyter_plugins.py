import sys

from .backends import jupyter

print("Loading plugins...")

parent_pkg = sys.modules[__package__]
parent_pkg.jupyter = jupyter
sys.modules[f"{__package__}.jupyter"] = jupyter
