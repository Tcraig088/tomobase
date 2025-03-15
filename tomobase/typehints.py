from tomobase.tiltschemes.tiltscheme import TiltScheme
from typing import Union, Tuple
import numpy as np

# either tiltscheme or nparray
TILTANGLETYPE = Union[Tuple[TiltScheme, int], np.ndarray]
