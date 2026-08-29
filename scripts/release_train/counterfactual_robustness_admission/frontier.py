from dataclasses import dataclass
from .refusal import refuse

@dataclass(frozen=True)
class CalibrationFrontier:
    calibrations: tuple
    def current(self):
        if not self.calibrations: refuse("EMPTY_CALIBRATION_FRONTIER")
        g=max(c.generation for c in self.calibrations)
        cur=[c for c in self.calibrations if c.generation==g]
        by_id={}
        for c in cur:
            old=by_id.get(c.estimator_id)
            if old and old.digest!=c.digest: refuse("DIVERGENT_CALIBRATION_FRONTIER")
            by_id[c.estimator_id]=c
        return tuple(by_id[k] for k in sorted(by_id))
    def require(self,c):
        cur={x.estimator_id:x for x in self.current()}
        x=cur.get(c.estimator_id)
        if x is None or x.generation!=c.generation or x.digest!=c.digest: refuse("STALE_CALIBRATION")
        return c
