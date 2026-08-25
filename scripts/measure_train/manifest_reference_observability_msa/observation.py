import re
from dataclasses import dataclass
from datetime import datetime
from .transport import TransportIdentity
from .refusal import Refused

STATUSES = {"RESOLVED", "TIMEOUT", "DNS_ERROR", "HTTP_ERROR", "UNSUPPORTED"}
RELATIONS = {"EXACT", "ADVANCED", "DIVERGED", "UNKNOWN"}

@dataclass(frozen=True, order=True)
class RefObservation:
    component_id: str
    transport: TransportIdentity
    status: str
    observed_at: datetime
    latency_ms: int
    observed_sha: str | None = None
    relation: str = "UNKNOWN"
    evidence_id: str = ""

    def __post_init__(self):
        if self.status not in STATUSES:
            raise Refused("REFUSED[INVALID_OBSERVATION_STATUS]")
        if self.relation not in RELATIONS:
            raise Refused("REFUSED[INVALID_REF_RELATION]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_OBSERVATION_TIME]")
        if self.latency_ms < 0:
            raise Refused("REFUSED[NEGATIVE_LATENCY]")
        if not self.evidence_id:
            raise Refused("REFUSED[EMPTY_EVIDENCE_ID]")
        if self.status == "RESOLVED":
            if not self.observed_sha or not re.fullmatch(r"[0-9a-f]{40}", self.observed_sha):
                raise Refused("REFUSED[RESOLVED_WITHOUT_EXACT_SHA]")
            if self.relation == "UNKNOWN":
                raise Refused("REFUSED[RESOLVED_WITH_UNKNOWN_RELATION]")
        else:
            if self.observed_sha is not None:
                raise Refused("REFUSED[CENSORED_WITH_SHA]")
            if self.relation != "UNKNOWN":
                raise Refused("REFUSED[CENSORED_WITH_RELATION]")
