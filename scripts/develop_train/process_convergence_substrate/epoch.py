from dataclasses import dataclass
from datetime import datetime, timezone
from .subject import SubjectEpoch
from .obligation import Obligation
from .refusal import Refused

@dataclass(frozen=True)
class ClosureEpoch:
    subject: SubjectEpoch
    at: datetime
    obligations: tuple[Obligation, ...]

    def __post_init__(self):
        if self.at.tzinfo is None or self.at.utcoffset() is None:
            raise Refused("NAIVE_TIME")
        keys=[o.key for o in self.obligations]
        if len(keys) != len(set(keys)):
            raise Refused("DUPLICATE_OBLIGATION")
        object.__setattr__(self, "at", self.at.astimezone(timezone.utc))
        object.__setattr__(self, "obligations", tuple(sorted(self.obligations, key=lambda o:o.key)))

    def by_key(self):
        return {o.key:o for o in self.obligations}
