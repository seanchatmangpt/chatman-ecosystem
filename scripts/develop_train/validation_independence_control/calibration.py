from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class Calibration:
    generation: int
    digest: str
    support: int
    coverage: Fraction
    miss_rate: Fraction
    mean_width: Fraction
    false_independent: Fraction
    false_dependent: Fraction
    def __post_init__(self):
        vals=(self.coverage,self.miss_rate,self.mean_width,self.false_independent,self.false_dependent)
        if self.generation<0 or len(self.digest)!=64 or self.support<1 or any(v<0 or v>1 for v in vals):
            raise Refused("INVALID_CALIBRATION")
    def admitted(self, min_support=8, min_coverage=Fraction(9,10), max_width=Fraction(1,2)):
        if self.support<min_support: raise Refused("INSUFFICIENT_CALIBRATION_SUPPORT")
        if self.coverage<min_coverage: raise Refused("CALIBRATION_UNRELIABLE")
        if self.mean_width>max_width: raise Refused("CALIBRATION_VACUOUS")
        return True
