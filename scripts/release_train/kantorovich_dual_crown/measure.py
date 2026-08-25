from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class FiniteMeasure:
    mass: tuple
    @classmethod
    def of(cls,mapping):
        if not mapping: raise Refused("EMPTY_MEASURE")
        vals=[]
        for k,v in sorted(mapping.items()):
            q=Fraction(v)
            if q<0: raise Refused("NEGATIVE_MASS",str(k))
            vals.append((str(k),q))
        total=sum((q for _,q in vals),Fraction())
        if total<=0: raise Refused("ZERO_MASS")
        return cls(tuple((k,q/total) for k,q in vals if q))
    def as_dict(self): return dict(self.mass)
    @property
    def support(self): return tuple(k for k,_ in self.mass)
