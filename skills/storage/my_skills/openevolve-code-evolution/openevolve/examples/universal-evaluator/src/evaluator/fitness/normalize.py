def normalize(value,*,minimum=None,maximum=None):
    if minimum is not None and maximum is not None:
        if maximum<=minimum: raise ValueError("maximum must be greater than minimum")
        return max(0.0,min(1.0,(value-minimum)/(maximum-minimum)))
    if 0<=value<=1: return value
    raise ValueError("metric without bounds must already be normalized to [0, 1]")
