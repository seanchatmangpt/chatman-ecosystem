from dataclasses import dataclass
from fractions import Fraction

from .errors import Refused


@dataclass(frozen=True)
class DependenceEvidence:
    generation: int
    digest: str
    overlap: Fraction
    phi: Fraction
    mutual_information: Fraction
    higher_order: Fraction = Fraction(0)

    def __post_init__(self):
        if self.generation < 0 or len(self.digest) != 64 or self.overlap < 0 or self.mutual_information < 0 or self.higher_order < 0:
            raise Refused("INVALID_DEPENDENCE")

    @property
    def independent(self):
        return self.overlap == 0 and self.phi == 0 and self.mutual_information == 0 and self.higher_order == 0
