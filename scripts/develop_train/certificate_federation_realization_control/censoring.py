from dataclasses import dataclass
from .observation import TransportState

@dataclass(frozen=True)
class Censoring:
    total: int
    resolved: int
    censored: int

    @property
    def fraction(self) -> float:
        return self.censored / self.total if self.total else 1.0

def census(observations) -> Censoring:
    values = tuple(observations)
    resolved = sum(o.state == TransportState.RESOLVED for o in values)
    return Censoring(len(values), resolved, len(values)-resolved)
