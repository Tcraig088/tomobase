import numpy as np

from ...core.base_classes.tiltscheme import TiltSchemeAbstract
from ...core.registers import tiltschemes
from ...core.log import logger

@tiltschemes.register(name='Binary Decomposition')
class Binary(TiltSchemeAbstract):
    """Binary acquisition tilt scheme.

    Stateful iterator: each call yields the next tilt angle and advances internal state.
    """

    def __init__(
        self,
        angle_min: float = -70,
        angle_max: float = 70,
        k: int = 8,
        isbidirectional: bool = True
    ):
        super().__init__(angle_min, angle_max)  # assumes your base stores start index + supports reset()
        self.k = int(k)
        self.isbidirectional = bool(isbidirectional)

        # immutable derived constants
        self._step0 = (self.angle_max - self.angle_min) / (self.k + 0.5)
        self._max_cutoff0 = self.angle_max - (self._step0 / 2)

        self._reset()

    def next_angle(self) -> float:
        if self.isbidirectional:
            angle = self._next_bidirectional()
        else:
            angle = self._next_unidirectional()
        return float(np.round(angle, 2))

    def _reset(self) -> None:
        # direction for bidirectional mode
        self._is_forward = True

        # running state
        self._i = 0  # step counter within this scheme (not the base index)
        self._offset = 0.0
        self._offset_set = 2
        self._offset_run = 1 / self._offset_set

        self._step = self._step0
        self._max_cutoff = self._max_cutoff0
        self._angle = 0.0

    def _next_bidirectional(self) -> float:
        if self._i == 0:
            self._angle = self.angle_min
            self._i += 1
            return self._angle

        if self._is_forward:
            # moving +step toward angle_max
            if np.isclose(self._angle + self._step, self.angle_max) or (self._angle + self._step) > self.angle_max:
                self._advance_offsets()
                self._is_forward = False

                # compute starting point on the return sweep
                candidate = self._max_cutoff + (self._step * self._offset)
                if np.isclose(candidate, self.angle_max) or candidate >= self.angle_max:
                    self._angle = candidate - self._step
                else:
                    self._angle = candidate

                self._step *= -1  # reverse direction
            else:
                self._angle = self._angle + self._step

        else:
            # moving -step toward angle_min
            if np.isclose(self._angle + self._step, self.angle_max) or (self._angle + self._step) < self.angle_min:
                self._advance_offsets()
                self._is_forward = True

                # start next forward sweep with new offset
                self._angle = self.angle_min + (abs(self._step) * self._offset)
                self._step *= -1  # reverse direction
            else:
                self._angle = self._angle + self._step

        self._i += 1
        return self._angle

    def _next_unidirectional(self) -> float:
        if self._i == 0:
            self._angle = self.angle_min
            self._i += 1
            return self._angle

        # move toward max; when you hit/past, advance offsets and restart near min
        if np.isclose(self._angle + self._step, self.angle_max) or (self._angle + self._step) > self.angle_max:
            self._advance_offsets()
            self._angle = self.angle_min + (self._step * self._offset)
        else:
            self._angle = self._angle + self._step

        self._i += 1
        return self._angle

    def _advance_offsets(self) -> None:
        """Update offset/offset_set/offset_run according to your original logic."""
        if (self._offset + 0.5) >= 1:
            if np.isclose(self._offset, (self._offset_set - 1) / self._offset_set):
                self._offset_set *= 2
                self._offset_run = 1 / self._offset_set
                self._offset = self._offset_run
            else:
                self._offset_run += 2 / self._offset_set
                self._offset = self._offset_run
        else:
            self._offset += 0.5