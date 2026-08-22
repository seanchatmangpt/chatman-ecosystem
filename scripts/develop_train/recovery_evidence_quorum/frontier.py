from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .evidence import RecoveryWitness
from .recovery import RecoveryAttempt
from .subject import Refused


@dataclass(frozen=True, slots=True)
class WitnessFrontier:
    current: tuple[RecoveryWitness, ...]
    historical: tuple[RecoveryWitness, ...]

    @classmethod
    def build(cls, attempt: RecoveryAttempt, witnesses: tuple[RecoveryWitness, ...], now: datetime) -> "WitnessFrontier":
        if now.tzinfo is None or now.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_FRONTIER_TIME]")
        seen: set[str] = set()
        current: list[RecoveryWitness] = []
        historical: list[RecoveryWitness] = []
        for witness in sorted(witnesses, key=lambda w: (w.observed_at, w.evidence_id)):
            if witness.evidence_id in seen:
                raise Refused("REFUSED[DUPLICATE_EVIDENCE_ID]")
            seen.add(witness.evidence_id)
            if witness.subject != attempt.consumer or witness.attempt_id != attempt.attempt_id:
                historical.append(witness)
            elif witness.observed_at > now:
                raise Refused("REFUSED[FUTURE_RECOVERY_EVIDENCE]")
            else:
                current.append(witness)
        return cls(tuple(current), tuple(historical))
