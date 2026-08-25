from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class Interval:
    lo: Fraction
    hi: Fraction
    def __post_init__(self):
        if not (0 <= self.lo <= self.hi <= 1): raise Refused("INVALID_EVIDENCE_INTERVAL")
    @classmethod
    def point(cls, x):
        x=Fraction(x); return cls(x,x)
    def conservative_and(self, other):
        return Interval(max(Fraction(0), self.lo+other.lo-1), min(self.hi, other.hi))
    def independent_and(self, other):
        return Interval(self.lo*other.lo, self.hi*other.hi)
    @property
    def width(self): return self.hi-self.lo
