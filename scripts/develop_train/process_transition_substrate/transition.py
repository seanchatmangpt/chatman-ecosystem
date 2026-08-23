from dataclasses import dataclass
from .subject_epoch import SubjectEpoch
from .errors import Refused
@dataclass(frozen=True)
class SubjectTransition:
    before: SubjectEpoch
    after: SubjectEpoch
    def __post_init__(self):
        if self.before.subject != self.after.subject: raise Refused("REFUSED[SUBJECT_DRIFT]")
        if self.after.generation != self.before.generation+1: raise Refused("REFUSED[NONCONTIGUOUS_GENERATION]")
