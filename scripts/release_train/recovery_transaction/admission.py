from __future__ import annotations
from datetime import datetime
from .attempt import RecoveryAttempt
from .context import RecoveryContext
from .witness import CompatibilityWitness, WitnessKind
from .subject import Refusal

def admit_attempt(attempt: RecoveryAttempt, current: RecoveryContext, witness: CompatibilityWitness|None, at: datetime, strategy: str) -> None:
    if not attempt.lease.active(at): raise Refusal("REFUSED[RECOVERY_ATTEMPT_EXPIRED]")
    if attempt.target_digest != current.digest: raise Refusal("REFUSED[RECOVERY_STALE_TARGET]")
    if strategy == "CAS_RESELECT": return
    if witness is None or not witness.passed or witness.before_digest != attempt.before_digest or witness.after_digest != attempt.target_digest:
        raise Refusal("REFUSED[RECOVERY_WITNESS_NOT_CURRENT]")
    if strategy == "VALIDATE_REBIND" and witness.kind not in {WitnessKind.EXACT,WitnessKind.SEMANTIC_EQUIVALENT}:
        raise Refusal("REFUSED[INSUFFICIENT_EQUIVALENCE_WITNESS]")
    if strategy not in {"VALIDATE_REBIND","REQUALIFY_ONLY"}: raise Refusal("REFUSED[UNKNOWN_RECOVERY_STRATEGY]")
