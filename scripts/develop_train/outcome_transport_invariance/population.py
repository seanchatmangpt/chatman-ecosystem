from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Population:
    name: str
    mass: tuple

    @classmethod
    def make(cls, name, mapping):
        if not name or not mapping:
            raise Refused("EMPTY_POPULATION")
        if any(float(v) < 0 for v in mapping.values()):
            raise Refused("NEGATIVE_MASS")
        total = sum(map(float, mapping.values()))
        if total <= 0:
            raise Refused("ZERO_MASS")
        return cls(name, tuple(sorted((str(k), float(v) / total) for k, v in mapping.items())))

    def data(self):
        return dict(self.mass)
