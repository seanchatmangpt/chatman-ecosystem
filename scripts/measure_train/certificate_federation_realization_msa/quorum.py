from dataclasses import dataclass
from .subject import Refused

@dataclass(frozen=True)
class QuorumRealization:
    required: int
    predicted_current: bool
    realized_current: bool
    exact_count: int

    @property
    def false_current(self):
        return self.predicted_current and not self.realized_current

    @property
    def false_stale(self):
        return (not self.predicted_current) and self.realized_current

def realize(observations, required):
    if required < 1:
        raise Refused("REFUSED[INVALID_QUORUM]")
    exact = sum(row.state == "RESOLVED" and row.relation == "EXACT" for row in observations)
    return exact >= required, exact
