from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused
@dataclass(frozen=True)
class Population:
    masses: tuple[tuple[str,Fraction],...]
    def __post_init__(self):
        keys=[k for k,_ in self.masses]
        if len(keys)!=len(set(keys)): raise Refused("REFUSED[DUPLICATE_POPULATION_CELL]")
        if any(v<0 for _,v in self.masses): raise Refused("REFUSED[NEGATIVE_POPULATION_MASS]")
        if sum((v for _,v in self.masses),Fraction(0))!=1:
            raise Refused("REFUSED[UNNORMALIZED_POPULATION]")
    def as_dict(self): return dict(self.masses)
