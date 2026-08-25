from dataclasses import dataclass
from datetime import datetime, timezone
from .identity import SubjectEpoch
from .obligation import Obligation
from .refusal import Refused

@dataclass(frozen=True)
class ClosureEpoch:
    subject: SubjectEpoch
    observed_at: datetime
    obligations: tuple[Obligation,...]
    def __post_init__(self):
        if self.observed_at.tzinfo is None: raise Refused("NAIVE_TIME")
        keys=[o.key for o in self.obligations]
        if len(keys)!=len(set(keys)): raise Refused("DUPLICATE_OBLIGATION")
    @property
    def universe(self): return tuple(sorted(o.key for o in self.obligations))
    @property
    def states(self): return {o.key:o.state for o in self.obligations}
