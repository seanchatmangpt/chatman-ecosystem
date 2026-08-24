from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from .errors import Refused

class TransportState(str, Enum):
    RESOLVED = "RESOLVED"
    TIMEOUT = "TIMEOUT"
    DNS = "DNS"
    HTTP_ERROR = "HTTP_ERROR"

class Relation(str, Enum):
    EXACT = "EXACT"
    ADVANCED = "ADVANCED"
    DIVERGED = "DIVERGED"
    CENSORED = "CENSORED"

@dataclass(frozen=True)
class Observation:
    observation_id: str
    certificate_generation: int
    transport_id: str
    implementation: str
    model: str
    domain: str
    state: TransportState
    predicted_current: bool
    realized_current: bool | None
    relation: Relation
    latency_ms: int
    methodology: str
    engine: str
    region: str
    evidence_root: str
    observed_at: datetime

    def __post_init__(self):
        if not self.observation_id or self.certificate_generation < 0:
            raise Refused("INVALID_OBSERVATION_IDENTITY")
        if self.latency_ms < 0:
            raise Refused("NEGATIVE_LATENCY")
        if self.observed_at.tzinfo is None:
            raise Refused("NAIVE_OBSERVATION_TIME")
        if any(not x for x in (self.transport_id, self.implementation, self.model, self.domain,
                               self.methodology, self.engine, self.region, self.evidence_root)):
            raise Refused("INCOMPLETE_OBSERVATION_PROVENANCE")
        if self.state != TransportState.RESOLVED:
            if self.relation != Relation.CENSORED or self.realized_current is not None:
                raise Refused("CENSORED_SEMANTIC_CLAIM")
        elif self.relation == Relation.CENSORED:
            raise Refused("RESOLVED_WITH_CENSORED_RELATION")

def admit(observations, generation: int):
    values = tuple(observations)
    if not values:
        raise Refused("EMPTY_FEDERATION_REALIZATION")
    ids = [o.observation_id for o in values]
    if len(ids) != len(set(ids)):
        raise Refused("DUPLICATE_OBSERVATION")
    now = datetime.now(timezone.utc)
    for o in values:
        if o.certificate_generation != generation:
            raise Refused("FOREIGN_CERTIFICATE_GENERATION")
        if o.observed_at > now:
            raise Refused("FUTURE_OBSERVATION")
    return tuple(sorted(values, key=lambda o: (o.observed_at, o.observation_id)))
