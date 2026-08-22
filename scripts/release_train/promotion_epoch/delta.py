from dataclasses import dataclass
from .subject import Subject
VALID={"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}
class DeltaRefusal(ValueError): pass
@dataclass(frozen=True)
class EvidenceDelta:
    before: Subject
    after: Subject
    before_state: str
    after_state: str
    changed: bool
    def __post_init__(self):
        if self.before.repo != self.after.repo: raise DeltaRefusal("REFUSED[FOREIGN_REPOSITORY_DELTA]")
        if self.before_state not in VALID or self.after_state not in VALID: raise DeltaRefusal("REFUSED[INVALID_EVIDENCE_STATE]")
        expected=(self.before.sha != self.after.sha) or (self.before_state != self.after_state)
        if self.changed != expected: raise DeltaRefusal("REFUSED[DELTA_CONTRADICTION]")
