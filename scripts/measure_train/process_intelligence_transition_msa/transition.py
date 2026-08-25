from dataclasses import dataclass
from .subject import SubjectEpoch, Refused

@dataclass(frozen=True, order=True)
class SubjectTransition:
    before: SubjectEpoch
    after: SubjectEpoch
    transition_id: str

    def __post_init__(self):
        if self.before.subject.repo != self.after.subject.repo:
            raise Refused("REFUSED[CROSS_REPOSITORY_SUBJECT_TRANSITION]")
        if self.before.subject.sha == self.after.subject.sha:
            raise Refused("REFUSED[NOOP_SUBJECT_TRANSITION]")
        if self.after.generation != self.before.generation + 1:
            raise Refused("REFUSED[NON_CONTIGUOUS_SUBJECT_GENERATION]")
        if not self.transition_id:
            raise Refused("REFUSED[EMPTY_TRANSITION_ID]")
