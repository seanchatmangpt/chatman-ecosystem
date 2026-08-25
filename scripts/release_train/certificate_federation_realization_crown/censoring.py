from dataclasses import dataclass
from .transport import Observation, TransportState

@dataclass(frozen=True)
class Census:
    total: int
    resolved: int
    censored: int

    @property
    def availability(self) -> float:
        return self.resolved/self.total if self.total else 0.0

def census(observations: tuple[Observation, ...]) -> Census:
    resolved=sum(o.state == TransportState.RESOLVED for o in observations)
    return Census(len(observations), resolved, len(observations)-resolved)
