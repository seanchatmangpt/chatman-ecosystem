from dataclasses import dataclass
from .subject import Subject, Refused

@dataclass(frozen=True)
class MeasurementIntent:
    subject: Subject
    candidate_ids: tuple
    frontier_digest: str
    strategy: str
    authority: str = "SELECT"
    def __post_init__(self):
        if not self.candidate_ids:
            raise Refused("REFUSED[EMPTY_MEASUREMENT_INTENT]")
        if self.authority != "SELECT":
            raise Refused("REFUSED[MEASUREMENT_INTENT_HAS_ACTUATION_AUTHORITY]")
        if len(self.frontier_digest)!=64:
            raise Refused("REFUSED[INVALID_FRONTIER_DIGEST]")
