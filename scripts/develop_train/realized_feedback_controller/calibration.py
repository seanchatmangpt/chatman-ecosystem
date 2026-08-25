from dataclasses import dataclass
from fractions import Fraction
from .trajectory import Trajectory

@dataclass(frozen=True)
class GainCalibration:
    support: int
    bias: Fraction
    mae: Fraction

    @classmethod
    def from_trajectory(cls, trajectory: Trajectory):
        residuals=trajectory.residuals
        n=len(residuals)
        return cls(n, sum(residuals, Fraction())/n, sum(abs(x) for x in residuals)/n)

    def admitted(self, *, min_support=3, max_mae=Fraction(1,4)):
        return self.support >= min_support and self.mae <= max_mae
