from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction

from .errors import Refused
from .subject import Subject


@dataclass(frozen=True)
class VisibilityObservation:
    subject: Subject
    observed_replicas: tuple[str, ...]
    known_replicas: tuple[str, ...]
    observed_at: datetime
    max_lag_seconds: int

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            raise Refused("NAIVE_OBSERVATION_TIME")
        if self.max_lag_seconds < 0:
            raise Refused("NEGATIVE_REPLICA_LAG")
        if len(set(self.known_replicas)) != len(self.known_replicas) or not self.known_replicas:
            raise Refused("INVALID_REPLICA_UNIVERSE")
        if len(set(self.observed_replicas)) != len(self.observed_replicas):
            raise Refused("DUPLICATE_REPLICA_OBSERVATION")
        if not set(self.observed_replicas).issubset(self.known_replicas):
            raise Refused("FOREIGN_REPLICA_OBSERVATION")

    @property
    def coverage(self) -> Fraction:
        return Fraction(len(self.observed_replicas), len(self.known_replicas))

    def require_current(self, now: datetime, max_age_seconds: int) -> None:
        if now.tzinfo is None or now < self.observed_at:
            raise Refused("INVALID_OBSERVATION_NOW")
        age = int((now.astimezone(timezone.utc) - self.observed_at.astimezone(timezone.utc)).total_seconds())
        if age > max_age_seconds:
            raise Refused("STALE_VISIBILITY_OBSERVATION")
