from .refusal import Refused
def current(calibrations):
    latest=max(c.generation for c in calibrations)
    xs=[c for c in calibrations if c.generation==latest]
    if len({c.digest for c in xs}) != 1: raise Refused("DIVERGENT_CURRENT_CALIBRATION")
    return xs[0]
