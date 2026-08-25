from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Feasibility:
    primal_dual_gap: Fraction
    max_dual_violation: Fraction
    max_slackness_residual: Fraction

    @property
    def exact(self) -> bool:
        return self.primal_dual_gap == 0 and self.max_dual_violation == 0 and self.max_slackness_residual == 0


def measure(certificate) -> Feasibility:
    return Feasibility(certificate.gap, certificate.max_dual_violation, certificate.max_slackness_residual)
