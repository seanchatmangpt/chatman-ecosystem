from dataclasses import dataclass
from datetime import datetime
from .subject import Refused
from .certificate import Certificate

STATES = {"RESOLVED", "TIMEOUT", "DNS_ERROR", "HTTP_ERROR"}
RELATIONS = {"EXACT", "ADVANCED", "DIVERGED", "CENSORED"}

@dataclass(frozen=True, order=True)
class Observation:
    certificate: Certificate
    transport_id: str
    implementation_digest: str
    model_digest: str
    domain: str
    state: str
    relation: str
    observed_sha: str | None
    latency_ms: int
    observed_at: datetime

    def __post_init__(self):
        if self.state not in STATES or self.relation not in RELATIONS:
            raise Refused("REFUSED[INVALID_OBSERVATION_STATE]")
        if self.observed_at.tzinfo is None:
            raise Refused("REFUSED[NAIVE_TIME]")
        if self.latency_ms < 0:
            raise Refused("REFUSED[NEGATIVE_LATENCY]")
        if self.state != "RESOLVED" and (self.relation != "CENSORED" or self.observed_sha is not None):
            raise Refused("REFUSED[CENSORED_SEMANTIC_CLAIM]")
        if self.state == "RESOLVED" and self.relation == "CENSORED":
            raise Refused("REFUSED[RESOLVED_WITHOUT_RELATION]")
        if self.state == "RESOLVED" and (self.observed_sha is None or len(self.observed_sha) != 40):
            raise Refused("REFUSED[INEXACT_OBSERVED_SHA]")
