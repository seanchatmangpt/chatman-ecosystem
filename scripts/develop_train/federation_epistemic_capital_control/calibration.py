from dataclasses import dataclass
from fractions import Fraction
import hashlib,json
from .directional import evaluate
from .errors import Refused
@dataclass(frozen=True)
class Calibration:
    generation:int; digest:str; support:int; effective_support:Fraction; false_current_rate:Fraction; false_stale_rate:Fraction; loss:Fraction
    @property
    def admitted(self): return self.effective_support>=3 and self.false_current_rate<=Fraction(1,5)
def calibrate(xs,generation,cap):
    r=evaluate(xs); body={'generation':generation,'support':r.support,'effective':str(cap.effective),'fc':r.false_current,'fs':r.false_stale,'loss':str(r.loss)}; d=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    return Calibration(generation,d,r.support,cap.effective,Fraction(r.false_current,r.support),Fraction(r.false_stale,r.support),r.loss)
def current(cs):
    cs=tuple(cs)
    if not cs: raise Refused("NO_EPISTEMIC_CALIBRATION")
    g=max(c.generation for c in cs); latest=[c for c in cs if c.generation==g]
    if len({c.digest for c in latest})!=1: raise Refused("SPLIT_EPISTEMIC_FRONTIER")
    return sorted(latest,key=lambda c:c.digest)[0]
