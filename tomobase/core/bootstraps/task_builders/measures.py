from ...data_classes import Measurement
from ...log import logger
from functools import wraps

def _wrap_measurements_validate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        measurements = kwargs.get("measurements", None)
        logger.trace("Wrapped Execution: Checking wether measurements are valid")
        if measurements is not None:
            if not isinstance(measurements, list):
                measurements = [measurements]
            
            for measurement in measurements:
                if not isinstance(measurement, Measurement):
                    raise ValueError("All items in the 'measurements' argument must be instances of a Measurement.")
        
        return func(*args, **kwargs)
    return wrapper

def _wrap_measurements_return(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.trace("Wrapped Execution: Adding new measurements to linked measurement list")
        measurements = kwargs.pop("measurements", None)
        results = func(*args, **kwargs)

        count_measurements = sum(isinstance(r, Measurement) for r in results)
        if measurements is not None:
            if count_measurements < len(measurements):
                raise ValueError(f"The number of measurements returned by the process ({count_measurements}) is less than the number of measurements provided ({len(measurements)}).")
            
            j = 0
            for i, result in enumerate(results):
                if isinstance(result, Measurement):
                    results[i] = measurements[j].stack(result)
                    j += 1

        return results
    return wrapper