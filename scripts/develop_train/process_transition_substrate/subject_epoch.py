from dataclasses import dataclass
import re
from .errors import Refused
_SUBJECT=re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
@dataclass(frozen=True, order=True)
class SubjectEpoch:
    subject: str
    generation: int
    def __post_init__(self):
        if not _SUBJECT.match(self.subject): raise Refused("REFUSED[INEXACT_SUBJECT]")
        if self.generation < 0: raise Refused("REFUSED[NEGATIVE_GENERATION]")
    def advance(self):
        return SubjectEpoch(self.subject, self.generation+1)
