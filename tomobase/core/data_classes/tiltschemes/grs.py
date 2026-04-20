
import numpy as np

from ...base_classes import TiltSchemeAbstract, TiltSchemeCursor
from ...registers import tiltschemes

@tiltschemes.register(name='GRS')  
class GRS(TiltSchemeAbstract):
    """Golden Ratio Sequence tilt scheme (infinite).

    Produces a quasi-uniform sampling over [angle_min, angle_max).
    """

    def __init__(
        self,
        angle_min: float = -70,
        angle_max: float = 70,
        start_at_zero: bool = True,
    ):
        super().__init__(angle_min, angle_max)

        self.start_at_zero = bool(start_at_zero)
        self._range_rad = np.radians(angle_max - angle_min)
        self._min_rad = np.radians(angle_min)
        self._gr = (1 + np.sqrt(5.0)) / 2.0

    def _angle_at_index(self, i: int) -> float:
        if i < 0:
            raise ValueError("GRS expects index >= 0.")

        angle_rad = np.mod(i * self._gr * self._range_rad, self._range_rad) + self._min_rad
        return float(np.round(np.degrees(angle_rad), 2))

    def angle_at(self, index: int) -> float:
        if index < 0:
            raise ValueError("GRS expects index >= 0.")

        offset = 0 if self.start_at_zero else 1
        return self._angle_at_index(index + offset)

    def is_finished(self, cursor: TiltSchemeCursor) -> bool:
        return False