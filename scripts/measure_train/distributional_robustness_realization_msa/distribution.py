from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True, order=True)
class Distribution:
    mass: tuple[tuple[str, Fraction], ...]
    def __post_init__(self):
        if not self.mass: raise Refused("REFUSED[EMPTY_DISTRIBUTION]")
        keys=[k for k,_ in self.mass]
        if len(keys)!=len(set(keys)): raise Refused("REFUSED[DUPLICATE_SUPPORT]")
        if any(v < 0 for _,v in self.mass): raise Refused("REFUSED[NEGATIVE_MASS]")
        if sum((v for _,v in self.mass), Fraction(0)) != 1: raise Refused("REFUSED[UNNORMALIZED_DISTRIBUTION]")
    def probability(self,key): return dict(self.mass).get(key,Fraction(0))
    @property
    def support(self): return frozenset(k for k,v in self.mass if v>0)
