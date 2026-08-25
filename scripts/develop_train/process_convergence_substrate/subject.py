from dataclasses import dataclass
import re
from .refusal import Refused

_SUBJECT_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")

@dataclass(frozen=True, order=True)
class SubjectEpoch:
    subject: str
    generation: int

    def __post_init__(self):
        if not _SUBJECT_RE.match(self.subject):
            raise Refused("INEXACT_SUBJECT", self.subject)
        if self.generation < 0:
            raise Refused("INVALID_GENERATION")

    def advance(self, subject: str) -> "SubjectEpoch":
        if subject == self.subject:
            raise Refused("NONADVANCING_SUBJECT")
        return SubjectEpoch(subject, self.generation + 1)
