from dataclasses import dataclass
from fractions import Fraction
from enum import Enum
from .geometry import total_variation, wasserstein1, chi_square
from .refusal import Refused
class Kind(str,Enum): TV="TV"; WASSERSTEIN="WASSERSTEIN"; CHI_SQUARE="CHI_SQUARE"
@dataclass(frozen=True)
class AmbiguitySet:
    kind: Kind; radius: Fraction; reference: object; ground_cost: dict|None=None
    def __post_init__(self):
        if self.radius < 0: raise Refused("INVALID_RADIUS")
    def distance(self,candidate):
        if self.kind is Kind.TV: return total_variation(candidate,self.reference)
        if self.kind is Kind.WASSERSTEIN: return wasserstein1(candidate,self.reference,self.ground_cost or {})
        if self.kind is Kind.CHI_SQUARE: return chi_square(candidate,self.reference)
        raise Refused("UNKNOWN_AMBIGUITY_KIND")
    def admits(self,candidate): return self.distance(candidate) <= self.radius
