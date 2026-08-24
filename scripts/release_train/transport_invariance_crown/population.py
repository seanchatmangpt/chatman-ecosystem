from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping
from .refusal import require

@dataclass(frozen=True)
class Population:
    mass: tuple[tuple[str, Fraction], ...]

    @classmethod
    def from_mapping(cls, values: Mapping[str, int | float | Fraction]) -> "Population":
        require(bool(values), "EMPTY_POPULATION")
        raw=[]
        for key,value in values.items():
            f=Fraction(value).limit_denominator(1_000_000)
            require(f >= 0, "NEGATIVE_POPULATION_MASS", key)
            raw.append((str(key), f))
        total=sum((v for _,v in raw), Fraction(0))
        require(total > 0, "ZERO_POPULATION_MASS")
        return cls(tuple(sorted((k, v/total) for k,v in raw)))

    def as_dict(self) -> dict[str, Fraction]:
        return dict(self.mass)

    def cells(self) -> tuple[str, ...]:
        return tuple(k for k,_ in self.mass)
