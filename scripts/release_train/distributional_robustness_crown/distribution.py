from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class Distribution:
    mass: tuple[tuple[str, Fraction], ...]
    @classmethod
    def from_mapping(cls, values):
        if not values: raise Refused("EMPTY_DISTRIBUTION")
        pairs=[]; total=Fraction(0)
        for k,v in sorted(values.items()):
            q=v if isinstance(v,Fraction) else Fraction(str(v))
            if q < 0: raise Refused("NEGATIVE_MASS", k)
            total += q; pairs.append((str(k),q))
        if total <= 0: raise Refused("ZERO_MASS")
        return cls(tuple((k,v/total) for k,v in pairs if v))
    def mapping(self): return dict(self.mass)
    @property
    def support(self): return frozenset(k for k,_ in self.mass)
