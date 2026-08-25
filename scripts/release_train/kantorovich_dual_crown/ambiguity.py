from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class AmbiguitySet:
    kind:str; radius:Fraction; generation:int
    def __post_init__(self):
        if self.kind not in {"W1","TV","CHI2"}: raise Refused("UNKNOWN_AMBIGUITY_KIND")
        if Fraction(self.radius)<0 or self.generation<0: raise Refused("INVALID_AMBIGUITY_SET")
