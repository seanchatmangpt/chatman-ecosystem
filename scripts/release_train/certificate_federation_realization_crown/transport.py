from dataclasses import dataclass
from enum import Enum
from .refusal import Refused
from .subject import Subject

class TransportState(str, Enum):
    RESOLVED="RESOLVED"; TIMEOUT="TIMEOUT"; DNS="DNS"; HTTP_ERROR="HTTP_ERROR"

class Relation(str, Enum):
    EXACT="EXACT"; ADVANCED="ADVANCED"; DIVERGED="DIVERGED"; CENSORED="CENSORED"

@dataclass(frozen=True)
class Observation:
    subject: Subject
    generation: int
    transport_id: str
    implementation: str
    model: str
    domain: str
    state: TransportState
    relation: Relation
    predicted_current: bool
    realized_current: bool | None
    observed_sha: str | None = None
    semantic_digest: str | None = None
    certificate_digest: str | None = None

    def __post_init__(self) -> None:
        if self.generation < 0 or not self.transport_id:
            raise Refused("INVALID_OBSERVATION_IDENTITY")
        censored = self.state != TransportState.RESOLVED
        if censored and self.relation != Relation.CENSORED:
            raise Refused("CENSORING_RELATION_MISMATCH")
        if censored and any((self.observed_sha, self.semantic_digest, self.certificate_digest, self.realized_current is not None)):
            raise Refused("CENSORED_SEMANTIC_CLAIM")
        if not censored and self.relation == Relation.CENSORED:
            raise Refused("RESOLVED_CANNOT_BE_CENSORED")
