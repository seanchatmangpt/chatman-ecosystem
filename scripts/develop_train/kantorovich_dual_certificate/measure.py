from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
@dataclass(frozen=True)
class FiniteMeasure:
    mass: tuple[tuple[str, Fraction], ...]
    @classmethod
    def from_mapping(cls, mapping):
        if not mapping:
            raise Refused("EMPTY_MEASURE")
        pairs = []
        total = Fraction(0)
        for key, value in sorted(mapping.items()):
            mass = Fraction(value)
            if mass < 0:
                raise Refused("NEGATIVE_MASS", str(key))
            if mass:
                pairs.append((str(key), mass))
                total += mass
        if total == 0:
            raise Refused("ZERO_TOTAL_MASS")
        return cls(tuple((key, mass / total) for key, mass in pairs))
    def as_dict(self):
        return dict(self.mass)
    @property
    def support(self):
        return tuple(key for key, _ in self.mass)
    def expectation(self, values):
        mapping = self.as_dict()
        missing = set(mapping) - set(values)
        if missing:
            raise Refused("MISSING_LOSS", ",".join(sorted(missing)))
        return sum((mass * Fraction(values[key]) for key, mass in mapping.items()), Fraction(0))
