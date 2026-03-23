import numpy as np

from ..core.registers import tiltschemes
from ..core.base_classes.tiltscheme import TiltSchemeAbstract

@tiltschemes.register(name='Incremental')
class Incremental(TiltSchemeAbstract):
    """Incremental Tilt Scheme (finite).

    Yields angles starting at angle_start, stepping by `step` until angle_end is reached.
    """

    def __init__(self, angle_min: float = -70, angle_max: float = 70, step: float = 2.0):
        super().__init__(angle_min, angle_max)   # if your base supports this; otherwise super().__init__(); self.index=index
        self.step = float(step)

        if self.step == 0:
            raise ValueError("step must be non-zero")

        # Direction sanity: step should move from start toward end
        if (self.angle_max > self.angle_min and self.step < 0) or (self.angle_max < self.angle_min and self.step > 0):
            raise ValueError("step sign does not move angle_start toward angle_end")

    def _angle_at_index(self, i: int) -> float:
        if i < 0:
            raise ValueError("index must be >= 0")

        angle = self.angle_min + (i * self.step)

        # Determine if this is the last valid angle (inclusive end)
        next_angle = angle + self.step
        if self.angle_max >= self.angle_min:
            if next_angle > self.angle_max + 1e-12:
                self._finished = True
        else:
            if next_angle < self.angle_max - 1e-12:
                self._finished = True

        return float(np.round(angle, 2))