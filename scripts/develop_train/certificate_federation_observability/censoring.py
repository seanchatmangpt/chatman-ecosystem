from dataclasses import dataclass
from .transport import TransportState

@dataclass(frozen=True)
class Censoring:
    resolved: int
    censored: int
    timeout: int
    dns: int
    http_error: int

    @property
    def fraction(self):
        total = self.resolved + self.censored
        return self.censored / total if total else 1.0

def summarize(observations):
    obs = tuple(observations)
    return Censoring(
        sum(o.state == TransportState.RESOLVED for o in obs),
        sum(o.state != TransportState.RESOLVED for o in obs),
        sum(o.state == TransportState.TIMEOUT for o in obs),
        sum(o.state == TransportState.DNS for o in obs),
        sum(o.state == TransportState.HTTP_ERROR for o in obs),
    )
