from .errors import Refused

class CalibrationFrontier:
    def __init__(self, calibrations):
        cs=tuple(calibrations)
        if not cs: raise Refused('EMPTY_CALIBRATION_FRONTIER')
        top=max(c.generation for c in cs); latest=[c for c in cs if c.generation==top]
        if len({c.digest for c in latest}) != 1: raise Refused('DIVERGENT_CALIBRATION_FRONTIER')
        self.current=latest[0]
    def require(self,generation,digest):
        if generation != self.current.generation or digest != self.current.digest: raise Refused('STALE_DECISION_CALIBRATION')
        return self.current
