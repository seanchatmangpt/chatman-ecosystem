from dataclasses import dataclass
from .probability import unit
from .errors import Refused

@dataclass(frozen=True)
class DecisionCalibration:
    generation:int
    digest:str
    support:int
    false_independent_rate:object
    false_dependent_rate:object
    defer_rate:object
    def __post_init__(self):
        if self.generation < 1: raise Refused('INVALID_CALIBRATION_GENERATION')
        if len(self.digest)!=64 or any(c not in '0123456789abcdef' for c in self.digest): raise Refused('INVALID_CALIBRATION_DIGEST')
        if self.support < 1: raise Refused('EMPTY_CALIBRATION_SUPPORT')
        for n in ('false_independent_rate','false_dependent_rate','defer_rate'):
            object.__setattr__(self,n,unit(getattr(self,n)))
    def admitted(self,min_support,max_fi,max_fd,max_defer):
        return self.support>=min_support and self.false_independent_rate<=unit(max_fi) and self.false_dependent_rate<=unit(max_fd) and self.defer_rate<=unit(max_defer)
