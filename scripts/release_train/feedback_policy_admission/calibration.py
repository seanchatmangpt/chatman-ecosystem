from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class GainCalibration:
    support: int
    bias: Fraction
    mae: Fraction
    @classmethod
    def from_residuals(cls,residuals):
        vals=tuple(residuals)
        if not vals: raise Refused("NO_CALIBRATION_EVIDENCE")
        n=len(vals)
        return cls(n, sum(vals,Fraction(0))/n, sum((abs(v) for v in vals),Fraction(0))/n)
    def admit(self, *, min_support=3, max_abs_bias=Fraction(1,5), max_mae=Fraction(1,4)):
        if self.support < min_support: raise Refused("UNDER_SUPPORTED_POLICY")
        if abs(self.bias) > max_abs_bias or self.mae > max_mae: raise Refused("UNRELIABLE_POLICY")
        return self
