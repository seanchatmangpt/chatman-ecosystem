from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused
@dataclass(frozen=True, order=True)
class Interval:
    lower: Fraction
    upper: Fraction
    def __post_init__(self):
        if self.lower < 0 or self.upper > 1 or self.lower > self.upper:
            raise Refused("REFUSED[INVALID_INTERVAL]")
    @property
    def width(self): return self.upper-self.lower
    def contains(self, x): return self.lower <= x <= self.upper
def frechet_and(a,b):
    return Interval(max(Fraction(0),a.lower+b.lower-1), min(a.upper,b.upper))
def independent_and(a,b):
    return Interval(a.lower*b.lower, a.upper*b.upper)
