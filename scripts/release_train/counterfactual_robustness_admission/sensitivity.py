from dataclasses import dataclass
from fractions import Fraction
from .refusal import refuse

@dataclass(frozen=True)
class Interval:
    lower: Fraction
    upper: Fraction
    def __post_init__(self):
        if self.lower<0 or self.upper>1 or self.lower>self.upper: refuse("INVALID_INTERVAL")
    @property
    def width(self): return self.upper-self.lower

def gamma_interval(point: Fraction, gamma: Fraction):
    if gamma < 1: refuse("INVALID_GAMMA")
    delta=(gamma-1)/gamma
    return Interval(max(Fraction(0),point-delta), min(Fraction(1),point+delta))

def breakdown_gamma(point: Fraction, threshold: Fraction, grid=(Fraction(1),Fraction(3,2),Fraction(2),Fraction(3),Fraction(4))):
    for g in grid:
        if gamma_interval(point,g).lower <= threshold:
            return g
    return grid[-1]+1
