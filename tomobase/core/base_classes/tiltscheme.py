from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
import numpy as np


class TiltSchemeAbstract(ABC):
    def __init__(self, angle_min: float = -70, angle_max: float = 70):
        self.angle_min = float(angle_min)
        self.angle_max = float(angle_max)

    @abstractmethod
    def angle_at(self, index: int) -> float:
        raise NotImplementedError

    def is_finished(self, cursor: "TiltSchemeCursor") -> bool:
        return False

    def __getitem__(self, item):
        if isinstance(item, int):
            return self.angle_at(item)

        if isinstance(item, slice):
            start = 0 if item.start is None else item.start
            step = 1 if item.step is None else item.step

            if item.stop is None:
                raise ValueError("Slice stop must be provided for an infinite tilt scheme.")

            return [self.angle_at(i) for i in range(start, item.stop, step)]

        raise TypeError(f"Invalid index type: {type(item)}")

    def cursor(self, start: int = 0) -> "TiltSchemeCursor":
        return TiltSchemeCursor(self, start=start)

    def __iter__(self) -> Iterator[float]:
        return self.cursor()


class TiltSchemeCursor(Iterator[float]):
    def __init__(self, scheme: TiltSchemeAbstract, start: int = 0):
        self.scheme = scheme
        self.start = int(start)
        self.index = int(start)
        self.angles: list[float] = []
        self._finished = False

    def __iter__(self):
        return self

    def __next__(self) -> float:
        if self._finished or self.scheme.is_finished(self):
            self._finished = True
            raise StopIteration

        angle = self.scheme.angle_at(self.index)
        self.angles.append(angle)
        self.index += 1
        return angle

    def reset(self):
        self.index = self.start
        self.angles.clear()
        self._finished = False

