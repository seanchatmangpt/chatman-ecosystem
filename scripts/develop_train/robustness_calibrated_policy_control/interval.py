from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True, order=True)
class Interval:
    lower:Fraction
    upper:Fraction
    def __post_init__(self):
        if self.lower>self.upper: raise Refused('REVERSED_INTERVAL')
    @property
    def width(self): return self.upper-self.lower
    @property
    def midpoint(self): return (self.lower+self.upper)/2
    def intersect(self, other:'Interval'):
        lo=max(self.lower,other.lower); hi=min(self.upper,other.upper)
        return None if lo>hi else Interval(lo,hi)
