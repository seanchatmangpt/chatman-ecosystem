from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class Quorum:
    threshold:Fraction; nominal:int; effective:Fraction
    @property
    def admitted(self): return self.effective>=self.threshold
def evaluate(cap,threshold):
    q=Quorum(Fraction(threshold),cap.nominal,cap.effective)
    if cap.nominal>=q.threshold and not q.admitted: raise Refused("PSEUDO_QUORUM",f"nominal={cap.nominal} effective={cap.effective}")
    return q
