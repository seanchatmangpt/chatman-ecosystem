from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class Calibration:
    generation:int; support:int; miss_rate:Fraction; mae:Fraction; digest:str; current:bool=True
    def __post_init__(self):
        if self.generation<0 or self.support<=0 or not (0<=Fraction(self.miss_rate)<=1) or Fraction(self.mae)<0 or len(self.digest)<8:
            raise Refused("INVALID_CALIBRATION")
def current(items):
    xs=[x for x in items if x.current]
    if not xs: raise Refused("NO_CURRENT_CALIBRATION")
    g=max(x.generation for x in xs); ys=[x for x in xs if x.generation==g]
    if len({x.digest for x in ys})!=1: raise Refused("DIVERGENT_CURRENT_CALIBRATION")
    return ys[0]
