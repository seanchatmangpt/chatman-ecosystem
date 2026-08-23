from .refusal import Refused
def current(calibrations, mode):
    xs=[c for c in calibrations if c.mode==mode]
    if not xs: raise Refused("MISSING_CALIBRATION")
    g=max(c.generation for c in xs); cur=[c for c in xs if c.generation==g]
    if len({c.digest for c in cur})!=1: raise Refused("DIVERGENT_CALIBRATION_FRONTIER")
    return cur[0]
