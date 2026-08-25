from dataclasses import dataclass
from datetime import datetime
from .subject import SubjectEpoch, Refused
from .obligation import STATES

@dataclass(frozen=True, order=True)
class ObligationEvidence:
    epoch: SubjectEpoch
    obligation_id: str
    source_id: str
    state: str
    observed_at: datetime
    receipt_sha256: str | None = None

    def __post_init__(self):
        if self.state not in STATES:
            raise Refused("REFUSED[INVALID_EVIDENCE_STATE]")
        if not self.obligation_id or not self.source_id:
            raise Refused("REFUSED[EMPTY_EVIDENCE_IDENTITY]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_EVIDENCE_TIME]")
        if self.receipt_sha256 is not None:
            if len(self.receipt_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.receipt_sha256):
                raise Refused("REFUSED[INVALID_EVIDENCE_RECEIPT]")
