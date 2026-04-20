from blinker import Signal
import time
import numbers
import numpy as np
from statsmodels.tsa.holtwinters import Holt


from .log import logger


def formatted_time(seconds):
    #format hh:mm:ss.ms
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{seconds:05.2f}"

class ProgressMetric:
    def __init__(self, name, criteria=0.0, is_less_than=False, units=''):
        self.name = name
        self.criteria = criteria
        self.is_less_than = is_less_than
        self.units = units
        self.value = None
        self._times = []
        self._values = []
    
    def update(self, value):
        self.value = value
        self._values.append(value)
        self._times.append(time.perf_counter())

class ProgressItem:
    def __init__(self, name, total=0, metric:ProgressMetric|None=None):
        self.name = name
        self.total = total
        self._is_iteration_estimated = False
        if total <= 0:
            self._is_iteration_estimated = True
            
        self.metric = metric
        if self.metric is None and self._is_iteration_estimated:
            raise ValueError("A metric must be provided if total is not positive.")
          
        self.i = 0
        self._time_start = time.perf_counter()
        self._time_elapsed = time.perf_counter() - self._time_start

        self.updated = Signal()
        self.completed = Signal()
        
    def update(self, value=None):
        if self._is_iteration_estimated:
            if isinstance(value, numbers.Number):
                self.metric.update(value)
            else:
                raise ValueError("A numeric value must be provided for estimated progress.")
        elif value is not None:
            logger.trace(f"Value {value} provided for non-criterion progress, ignoring.")
        
        self._time_elapsed = time.perf_counter() - self._time_start
        self.i += 1
        self.updated.send(info=self)
        
        if self.i >= self.total:
            self.complete()
        
    def complete(self):
        self.i = self.total
        self._time_elapsed = time.perf_counter() - self._time_start
        self.completed.send(bar=self)
    
    def time_elapsed(self):
        return formatted_time(self._time_elapsed)
     
    def time_remaining(self):
        if self.i == 0:
            return formatted_time(0.00)
        
        if self._is_iteration_estimated:
            crossing, reliability = self.estimate_crossing_and_reliability()
            if crossing is not None:
                progress_fraction = self.i / (crossing + self.i)
                time_estimate = self._time_elapsed * (1 - progress_fraction) / progress_fraction
                return f"{formatted_time(time_estimate)} {reliability}"
            return f"??:??:?? {reliability}"
        
        else:
            progress_fraction = self.i / self.total
            return formatted_time(self._time_elapsed * (1 - progress_fraction) / progress_fraction)

    
    def estimate_crossing_and_reliability(self):
        threshold = self.metric.criteria
        horizon = 500
        holdout = 5
        
        y = np.asarray(self.metric._values, dtype=float)
        if len(y) < max(8, holdout + 3):
            return None, "x"

        train = y[:-holdout]
        test = y[-holdout:]

        fit = Holt(train, initialization_method="estimated").fit(optimized=True)
        pred = fit.forecast(holdout)
        mae = float(np.mean(np.abs(pred - test)))

        fit_full = Holt(y, initialization_method="estimated").fit(optimized=True)
        forecast = fit_full.forecast(horizon)

        cross = None
        for step, val in enumerate(forecast, start=1):
            if (self.metric.is_less_than and val < threshold) or (not self.metric.is_less_than and val > threshold):
                cross = step
                break

        if cross is None:
            self.total = None
            return None, "x"

        gap = abs(y[-1] - threshold)
        # Metric based progress will be explicitly finished by the user so that they can do all tolerance and precision checks themselves.
        # Therefore, if the metric is close enough to the criteria, we can consider it as good as finished but will add a couple iterations for safety.
        if gap <= 0.0 + 1e-8:
            self.total = self.i + cross
            return 3, "~~"

        self.total = self.i + cross
        ratio = mae / gap
        if ratio < 0.25:
            reliability = "^"
        elif ratio < 0.75:
            reliability = "~"
        else:
            reliability = "v"
        return cross, reliability

    def __iter__(self):
        if self._is_iteration_estimated:
            raise TypeError(
                "Cannot iterate ProgressInfo directly when total is unknown. "
                "Use progress(iterable) instead."
            )

        for i in range(self.total):
            yield i
            self.update()

class ProgressHandler:
    def __init__(self):
        
        self._progress_bars = {}
        self.progress_updated = Signal()
        self.progress_completed = Signal()
        self.progress_created = Signal()
        
    def new(self, name, *args, **kwargs):
        self._progress_bars[name] = ProgressItem(name, *args, **kwargs)
        self.progress_created.send(name=name, info=self._progress_bars[name])
        
        bar = self._progress_bars[name]
        bar.completed.connect(self._on_delete, weak=False)
        return self._progress_bars[name]
    
    def _on_delete(self, sender, bar):
        name = bar.name
        if name in self._progress_bars:
            del self._progress_bars[name]
            
progress = ProgressHandler()