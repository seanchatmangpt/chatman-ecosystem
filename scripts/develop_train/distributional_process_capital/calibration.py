from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class Calibration:
    generation:int
    digest:str
    support:int
    misses:int
    mean_width:Fraction
    def __post_init__(self):
        if self.generation<0 or self.support<0 or self.misses<0 or self.misses>self.support or len(self.digest)!=64:
            raise Refused("INVALID_CALIBRATION")
    @property
    def miss_rate(self):
        return Fraction(self.misses,self.support) if self.support else Fraction(1)
    def admitted(self,min_support=5,max_miss=Fraction(1,5),max_width=Fraction(1,2)):
        return self.support>=min_support and self.miss_rate<=max_miss and self.mean_width<=max_width

def current(calibrations):
    cs=tuple(calibrations)
    if not cs:
        raise Refused("NO_CALIBRATION_FRONTIER")
    generation=max(c.generation for c in cs)
    latest=[c for c in cs if c.generation==generation]
    if len({c.digest for c in latest})!=1:
        raise Refused("DIVERGENT_CURRENT_CALIBRATION")
    return sorted(latest,key=lambda c:c.digest)[0]
