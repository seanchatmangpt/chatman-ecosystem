from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class Distribution:
    mass: tuple[tuple[str, Fraction], ...]
    @classmethod
    def from_mapping(cls, mapping):
        if not mapping:
            raise Refused("EMPTY_DISTRIBUTION")
        rows=[]
        for key,value in mapping.items():
            q=Fraction(value)
            if q < 0:
                raise Refused("NEGATIVE_MASS", str(key))
            rows.append((str(key),q))
        total=sum((q for _,q in rows), Fraction(0))
        if total <= 0:
            raise Refused("ZERO_TOTAL_MASS")
        return cls(tuple(sorted((k,q/total) for k,q in rows if q > 0)))
    def get(self,key):
        return dict(self.mass).get(key, Fraction(0))
    @property
    def support(self):
        return frozenset(k for k,_ in self.mass)
