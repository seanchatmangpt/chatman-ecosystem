from dataclasses import dataclass
from .errors import Refused
@dataclass(frozen=True)
class Interval:
    lo: float
    hi: float
    def __post_init__(self):
        if not (0 <= self.lo <= self.hi <= 1): raise Refused('REFUSED[INVALID_INTERVAL]')
    def frechet_and(self, other):
        return Interval(max(0.0,self.lo+other.lo-1.0), min(self.hi,other.hi))
    def independent_and(self, other):
        return Interval(self.lo*other.lo,self.hi*other.hi)
    @property
    def width(self): return self.hi-self.lo
