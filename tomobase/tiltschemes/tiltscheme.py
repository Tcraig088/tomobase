from abc import ABC, abstractmethod
from collections.abc import Iterator
import numpy as np

class TiltScheme(ABC, Iterator[float]):
    def __init__(self, angle_min: float = -70, angle_max: float = 70):
        self.angle_min = float(angle_min)
        self.angle_max = float(angle_max)
        self.index = 0
        self._finished = False
        
        self.current_angle = self.next_angle()
        self.angles = np.array([])
        self.reset()

    def __iter__(self):
        return self

    def __next__(self) -> float:
        if self._finished:
            raise StopIteration
        angle = self.next_angle()
        self.angles = np.append(self.angles, angle)
        self.index += 1
        return angle

    @abstractmethod
    def next_angle(self) -> float:
        """Return next angle and update any internal state."""
        pass
    
    
    def generate_angles_from_slice(self, sl: slice) -> list[float]:
        index = self.index
        self.reset()
        _list = []
        for i in range(sl.start, sl.stop):
            try:
                self.current_angle = next(self)
                if i in range(sl.start, sl.stop, sl.step):
                    np.array(_list.append(self.current_angle))
            except StopIteration:
                break
        self.index = index
        return _list
    
    def generate_angles(self, n: int) -> list[float]:
        out = []
        for _ in range(n):
            try:
                out.append(next(self))
            except StopIteration:
                break
        return out
    
    def reset(self):
        self.index = 0
        self.angles = np.array([])
        self._finished = False