from dataclasses import dataclass
from fractions import Fraction
from .trajectory import Trajectory

@dataclass(frozen=True)
class Hazard:
    discharges: int
    regressions: int
    @property
    def balance(self): return Fraction(self.discharges-self.regressions, max(1,self.discharges+self.regressions))

def hazards(t: Trajectory) -> Hazard:
    d=r=0
    for a,b in zip(t.epochs,t.epochs[1:]):
        for key in t.current.universe:
            av,bv=int(a.states[key]),int(b.states[key])
            if bv<av:d+=1
            elif bv>av:r+=1
    return Hazard(d,r)
