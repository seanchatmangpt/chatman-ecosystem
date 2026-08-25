from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
from .obligation import ObligationState

@dataclass(frozen=True, order=True)
class ClosureEpoch:
    subject: Subject
    observed_at: datetime
    obligations: tuple[ObligationState, ...]
    def __post_init__(self):
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_EPOCH_TIME]")
        ids=[o.obligation_id for o in self.obligations]
        if len(ids) != len(set(ids)): raise Refused("REFUSED[DUPLICATE_OBLIGATION]")
