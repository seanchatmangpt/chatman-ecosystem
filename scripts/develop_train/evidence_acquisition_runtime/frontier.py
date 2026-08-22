from dataclasses import dataclass
import hashlib,json
from .subject import Refusal
@dataclass(frozen=True, slots=True)
class CalibrationFrontier:
    generation:int; digest:str
    @classmethod
    def build(cls,calibrations):
        if not calibrations: raise Refusal('REFUSED_EMPTY_CALIBRATION_FRONTIER')
        g=max(c.generation for c in calibrations); current=[c for c in calibrations if c.generation==g]; ids=[c.candidate_id for c in current]
        if len(ids)!=len(set(ids)): raise Refusal('REFUSED_DIVERGENT_CALIBRATION_FRONTIER')
        body=[(c.candidate_id,c.generation,c.support,str(c.true_positive_rate),str(c.false_positive_rate),c.observed_at.isoformat()) for c in sorted(current,key=lambda x:x.candidate_id)]
        return cls(g,hashlib.sha256(json.dumps(body,separators=(',',':')).encode()).hexdigest())
    def assert_current(self,current):
        if self!=current: raise Refusal('REFUSED_STALE_CALIBRATION_FRONTIER')
