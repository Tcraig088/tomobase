import dataclasses
from ..environment import EnvironmentContext 

@dataclasses.dataclass
class ProcessVariables():
    inplace: bool
    verbose_outputs: bool
    measurements: list | None
    proxy: EnvironmentContext
    restore_context: bool