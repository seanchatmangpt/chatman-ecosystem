from dataclasses import dataclass
from datetime import datetime
from .subject_epoch import SubjectEpoch
from .obligation import Obligation
from .errors import Refused
@dataclass(frozen=True)
class Evidence:
    epoch: SubjectEpoch
    obligation: Obligation
    observed_at: datetime
    digest: str
    def __post_init__(self):
        if self.observed_at.tzinfo is None: raise Refused("REFUSED[NAIVE_TIME]")
        if len(self.digest)!=64 or any(c not in "0123456789abcdef" for c in self.digest): raise Refused("REFUSED[INVALID_DIGEST]")
def admit(e: Evidence, current: SubjectEpoch):
    if e.epoch.subject != current.subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
    if e.epoch.generation != current.generation: raise Refused("REFUSED[STALE_OR_FUTURE_EVIDENCE]")
    return e
