from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from .errors import Refused
from .geometry import total_variation, chi_square
from .wasserstein import wasserstein1
class Kind(str,Enum):
    TV="TV"; WASSERSTEIN="WASSERSTEIN"; CHI_SQUARE="CHI_SQUARE"
@dataclass(frozen=True)
class AmbiguitySet:
    center: object
    kind: Kind
    radius: Fraction
    ground_cost: dict|None=None
    def __post_init__(self):
        if self.radius<0:
            raise Refused("NEGATIVE_AMBIGUITY_RADIUS")
    def distance(self,candidate):
        if self.kind==Kind.TV:
            return total_variation(self.center,candidate)
        if self.kind==Kind.WASSERSTEIN:
            return wasserstein1(self.center,candidate,self.ground_cost or {})
        return chi_square(candidate,self.center)
    def contains(self,candidate):
        return self.distance(candidate)<=self.radius
    def require(self,candidate):
        if not self.contains(candidate):
            raise Refused("OUTSIDE_AMBIGUITY_SET")
        return candidate
