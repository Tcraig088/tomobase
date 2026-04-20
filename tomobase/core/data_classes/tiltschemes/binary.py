import numpy as np
from collections.abc import Iterable, Iterator

from ...base_classes import TiltSchemeAbstract, TiltSchemeCursor
from ...registers import tiltschemes


class BinaryCursor(TiltSchemeCursor):
    """Stateful cursor for Binary scheme.

    This holds the mutable recurrence state that used to live on the scheme.
    """

    def __init__(self, scheme: TiltSchemeAbstract, start: int = 0):
        super().__init__(scheme, start=start)
        self._is_forward = True
        self._i = 0
        self._offset = 0.0
        self._offset_set = 2
        self._offset_run = 1 / self._offset_set

        self._step = self.scheme._step0
        self._max_cutoff = self.scheme._max_cutoff0
        self._angle = 0.0

        for _ in range(start):
            next(self)

    def __iter__(self):
        return self

    def __next__(self) -> float:
        if self._finished:
            raise StopIteration

        if self.scheme.isbidirectional:
            angle = self._next_bidirectional()
        else:
            angle = self._next_unidirectional()

        angle = float(np.round(angle, 2))
        self.angles.append(angle)
        self.index += 1
        return angle

    def reset(self):
        self.index = 0
        self.angles.clear()
        self._finished = False

        self._is_forward = True
        self._i = 0
        self._offset = 0.0
        self._offset_set = 2
        self._offset_run = 1 / self._offset_set

        self._step = self.scheme._step0
        self._max_cutoff = self.scheme._max_cutoff0
        self._angle = 0.0

        for _ in range(self.start):
            next(self)

    def _advance_offsets(self) -> None:
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

    def _next_bidirectional(self) -> float:
        if self._i == 0:
            self._angle = self.scheme.angle_min
            self._i += 1
            return self._angle

        if self._is_forward:
            if np.isclose(self._angle + self._step, self.scheme.angle_max) or (
                self._angle + self._step
            ) > self.scheme.angle_max:
                self._advance_offsets()
                self._is_forward = False

                candidate = self._max_cutoff + (self._step * self._offset)
                if np.isclose(candidate, self.scheme.angle_max) or candidate >= self.scheme.angle_max:
                    self._angle = candidate - self._step
                else:
                    self._angle = candidate

                self._step *= -1
            else:
                self._angle = self._angle + self._step

        else:
            if np.isclose(self._angle + self._step, self.scheme.angle_max) or (
                self._angle + self._step
            ) < self.scheme.angle_min:
                self._advance_offsets()
                self._is_forward = True
                self._angle = self.scheme.angle_min + (abs(self._step) * self._offset)
                self._step *= -1
            else:
                self._angle = self._angle + self._step

        self._i += 1
        return self._angle

    def _next_unidirectional(self) -> float:
        if self._i == 0:
            self._angle = self.scheme.angle_min
            self._i += 1
            return self._angle

        if np.isclose(self._angle + self._step, self.scheme.angle_max) or (
            self._angle + self._step
        ) > self.scheme.angle_max:
            self._advance_offsets()
            self._angle = self.scheme.angle_min + (self._step * self._offset)
        else:
            self._angle = self._angle + self._step

        self._i += 1
        return self._angle

@tiltschemes.register(name='Binary Decomposition')
class Binary(TiltSchemeAbstract):
    """Binary acquisition tilt scheme.

    Stateless externally, but uses an internal cache plus BinaryCursor.
    """

    def __init__(
        self,
        angle_min: float = -70,
        angle_max: float = 70,
        k: int = 8,
        isbidirectional: bool = True,
    ):
        super().__init__(angle_min, angle_max)

        self.k = int(k)
        self.isbidirectional = bool(isbidirectional)

        if self.k <= 0:
            raise ValueError("k must be > 0")

        self._step0 = (self.angle_max - self.angle_min) / (self.k + 0.5)
        self._max_cutoff0 = self.angle_max - (self._step0 / 2)

        self._cache: list[float] = []

    def cursor(self, start: int = 0) -> BinaryCursor:
        return BinaryCursor(self, start=start)

    def angle_at(self, index: int) -> float:
        if index < 0:
            raise ValueError("index must be >= 0")

        if index < len(self._cache):
            return self._cache[index]

        cursor = self.cursor(start=len(self._cache))
        while len(self._cache) <= index:
            self._cache.append(next(cursor))

        return self._cache[index]

    def is_finished(self, cursor: TiltSchemeCursor) -> bool:
        return False
    
