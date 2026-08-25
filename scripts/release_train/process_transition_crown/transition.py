from dataclasses import dataclass
from .subject import SubjectEpoch
from .refusal import Refused

@dataclass(frozen=True)
class SubjectTransition:
    before: SubjectEpoch
    after: SubjectEpoch

    def __post_init__(self) -> None:
        if self.before.repo != self.after.repo:
            raise Refused("FOREIGN_TRANSITION")
        if self.after.generation != self.before.generation + 1:
            raise Refused("NONCONTIGUOUS_TRANSITION")
        if self.after.sha == self.before.sha:
            raise Refused("NONADVANCING_TRANSITION")
