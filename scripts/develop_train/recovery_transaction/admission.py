from __future__ import annotations
from datetime import datetime
from .attempt import RecoveryAttempt
from .context import RecoveryContext
from .witness import CompatibilityWitness
from .subject import Refusal

def admit_attempt(attempt: RecoveryAttempt, current: RecoveryContext, witness: CompatibilityWitness | None, now: datetime) -> None:
    if not attempt.lease.active(now):
        raise Refusal("RECOVERY_LEASE_EXPIRED", "attempt lease is not active")
    if attempt.target_context.digest != current.digest:
        raise Refusal("RECOVERY_STALE_TARGET", "target context is no longer current")
    if attempt.base_context.digest == attempt.target_context.digest:
        return
    if witness is None:
        raise Refusal("RECOVERY_WITNESS_REQUIRED", "changed context requires witness")
    if witness.before_digest != attempt.base_context.digest or witness.after_digest != current.digest:
        raise Refusal("STALE_RECOVERY_WITNESS", "witness does not bind exact current transition")
    if witness.result != "PASS":
        raise Refusal("RECOVERY_WITNESS_NOT_PASSING", witness.result)
