from __future__ import annotations
from dataclasses import dataclass
from .attempt import RecoveryAttempt
from .subject import Refusal

@dataclass(frozen=True)
class AttemptFrontier:
    current: tuple[RecoveryAttempt, ...]
    historical: tuple[RecoveryAttempt, ...]
    @classmethod
    def build(cls, attempts: list[RecoveryAttempt]) -> "AttemptFrontier":
        if not attempts:
            return cls((), ())
        by_id = {}
        for attempt in attempts:
            by_id.setdefault(attempt.attempt_id, attempt)
        unique = list(by_id.values())
        top = max(attempt.ordinal for attempt in unique)
        current = tuple(sorted((attempt for attempt in unique if attempt.ordinal == top), key=lambda attempt: attempt.attempt_id))
        if len({attempt.target_context.digest for attempt in current}) > 1:
            raise Refusal("DIVERGENT_RECOVERY_FRONTIER", "max ordinal targets diverge")
        historical = tuple(sorted((attempt for attempt in unique if attempt.ordinal < top), key=lambda attempt: (attempt.ordinal, attempt.attempt_id)))
        return cls(current, historical)
