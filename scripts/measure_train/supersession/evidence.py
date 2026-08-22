from dataclasses import dataclass
from .subject import Subject, Refused
from .epoch import Epoch

KINDS = {"CI", "RUNTIME", "ARTIFACT", "RECEIPT", "DEPENDENCY", "STATUS"}
OUTCOMES = {"PASS", "FAIL", "PENDING", "UNKNOWN", "UNSUPPORTED"}

@dataclass(frozen=True, order=True)
class Evidence:
    subject: Subject
    epoch: Epoch
    kind: str
    scope: str
    source_id: str
    outcome: str

    def __post_init__(self):
        if self.kind not in KINDS:
            raise Refused("REFUSED[UNKNOWN_EVIDENCE_KIND]")
        if self.outcome not in OUTCOMES:
            raise Refused("REFUSED[INVALID_OUTCOME]")
        if not self.scope.strip():
            raise Refused("REFUSED[EMPTY_SCOPE]")
        if not self.source_id.strip():
            raise Refused("REFUSED[EMPTY_SOURCE_ID]")
