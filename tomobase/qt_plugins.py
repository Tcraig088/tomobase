import sys

from .backends import qt

print("Loading plugins...")

parent_pkg = sys.modules[__package__]
parent_pkg.qt = qt
sys.modules[f"{__package__}.qt"] = qt
