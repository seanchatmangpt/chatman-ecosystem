from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Feasibility:
    duality_gap: Fraction
    feasibility_residual: Fraction
    slackness_residual: Fraction
    @property
    def exact(self): return self.duality_gap == self.feasibility_residual == self.slackness_residual == 0
def measure(c):
    return Feasibility(abs(c.primal-c.dual), c.feasibility_residual, c.slackness_residual)
