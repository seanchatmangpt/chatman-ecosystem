from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

@dataclass(frozen=True)
class Population:
    name: str
    mass: tuple[tuple[str, Fraction], ...]
    def __post_init__(self):
        if not self.name or not self.mass: raise Refused("INVALID_POPULATION")
        total=sum((v for _,v in self.mass), Fraction(0))
        if any(v < 0 for _,v in self.mass) or total != 1:
            raise Refused("POPULATION_NOT_NORMALIZED", self.name)
        if len({k for k,_ in self.mass}) != len(self.mass): raise Refused("DUPLICATE_POPULATION_CELL")
    def as_dict(self): return dict(self.mass)
