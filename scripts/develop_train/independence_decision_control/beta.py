from dataclasses import dataclass
from fractions import Fraction

from .errors import Refused


@dataclass(frozen=True)
class BetaEvidence:
    independent: int
    dependent: int

    def __post_init__(self):
        if self.independent < 0 or self.dependent < 0:
            raise Refused("INVALID_EVIDENCE")

    @property
    def alpha(self):
        return self.independent + 1

    @property
    def beta(self):
        return self.dependent + 1

    @property
    def mean_independent(self):
        return Fraction(self.alpha, self.alpha + self.beta)

    @property
    def support(self):
        return self.independent + self.dependent
