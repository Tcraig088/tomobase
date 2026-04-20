import numpy as np

from ...registers import tiltschemes
from ...base_classes import TiltSchemeAbstract, TiltSchemeCursor

@tiltschemes.register(name='Incremental')
class Incremental(TiltSchemeAbstract):
    """Incremental Tilt Scheme (finite).

    Yields angles starting at angle_min, stepping by `step`
    until angle_max is reached inclusively.
    """

    def __init__(
        self,
        angle_min: float = -70,
        angle_max: float = 70,
        step: float = 2.0,
    ):
        super().__init__(angle_min, angle_max)
        self.step = float(step)

        if self.step == 0:
            raise ValueError("step must be non-zero")

        # Step must move from angle_min toward angle_max.
        if (self.angle_max > self.angle_min and self.step < 0) or (
            self.angle_max < self.angle_min and self.step > 0
        ):
            raise ValueError("step sign does not move angle_min toward angle_max")

    def _angle_at_index(self, i: int) -> float:
        if i < 0:
            raise ValueError("index must be >= 0")

        angle = self.angle_min + (i * self.step)
        return float(np.round(angle, 2))

    def angle_at(self, index: int) -> float:
        if index < 0:
            raise ValueError("index must be >= 0")
        return self._angle_at_index(index)

    def is_finished(self, cursor: TiltSchemeCursor) -> bool:
        angle = self._angle_at_index(cursor.index)

        if self.angle_max >= self.angle_min:
            return angle > self.angle_max + 1e-12
        else:
            return angle < self.angle_max - 1e-12