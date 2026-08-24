from dataclasses import dataclass
import hashlib, json
from .dwell import zero_red
from .errors import Refused
@dataclass(frozen=True)
class Calibration:
    generation: int
    support: int
    false_fixed_rate: float
    false_nonfixed_rate: float
    digest: str
    @property
    def admitted(self): return self.support >= 5 and self.false_fixed_rate <= 0.2
def calibrate(observations,generation):
    obs=tuple(observations)
    if len(obs)<2: raise Refused("INSUFFICIENT_CALIBRATION_SUPPORT")
    ff=sum(o.controller_claim_fixed and not zero_red(o) for o in obs)
    fn=sum((not o.controller_claim_fixed) and zero_red(o) for o in obs)
    body={"generation":generation,"support":len(obs),"ff":ff,"fn":fn}
    digest=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return Calibration(generation,len(obs),ff/len(obs),fn/len(obs),digest)
def current(calibrations):
    cs=tuple(calibrations)
    if not cs: raise Refused("NO_CONVERGENCE_CALIBRATION")
    g=max(c.generation for c in cs); latest=[c for c in cs if c.generation==g]
    if len({c.digest for c in latest}) != 1: raise Refused("SPLIT_CONVERGENCE_CALIBRATION")
    return latest[0]
