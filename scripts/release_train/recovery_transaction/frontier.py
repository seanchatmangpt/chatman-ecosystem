from __future__ import annotations
from dataclasses import dataclass
from .attempt import RecoveryAttempt
from .subject import Refusal
@dataclass(frozen=True)
class AttemptFrontier:
    current: RecoveryAttempt
    historical: tuple[RecoveryAttempt, ...]
    @classmethod
    def build(cls, attempts: list[RecoveryAttempt]) -> "AttemptFrontier":
        if not attempts: raise Refusal("REFUSED[EMPTY_RECOVERY_FRONTIER]")
        maximum=max(a.ordinal for a in attempts)
        maxima=[a for a in attempts if a.ordinal==maximum]
        ids={a.attempt_id for a in maxima}
        if len(ids)!=1: raise Refusal("REFUSED[DIVERGENT_RECOVERY_FRONTIER]")
        current=sorted(maxima,key=lambda a:a.attempt_id)[0]
        return cls(current, tuple(sorted((a for a in attempts if a.attempt_id!=current.attempt_id), key=lambda a:(a.ordinal,a.attempt_id))))
