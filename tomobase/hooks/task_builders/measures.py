from ...data import Analysis

def _wrap_measure(func):
    def wrapper(*args, **kwargs):
        measurements = kwargs.get("measurements", [])
        if not isinstance(measurements, list):
            measurements = [measurements]
        
        for measurement in measurements:
            if not isinstance(measurement, Analysis):
                raise ValueError("All items in the 'measurements' argument must be instances of a Measurement.")
        
        results = func(*args, **kwargs)
        if isinstance(results, tuple):
            count_measurements = sum(isinstance(r, Analysis) for r in results)
        else: 
            count_measurements = 1 if isinstance(results, Analysis) else 0

        if count_measurements < len(measurements):
            raise ValueError(f"The number of measurements returned by the process ({count_measurements}) is less than the number of measurements provided ({len(measurements)}).")
        
        j = 0
        for i, result in enumerate(results):
            if isinstance(result, Analysis):
                results[i] = measurements[j].stack(result)
                j += 1

        return results