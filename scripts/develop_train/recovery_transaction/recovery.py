from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .attempt import RecoveryAttempt
from .witness import CompatibilityWitness, WitnessKind
from .subject import Refusal

class RecoveryStrategy(str, Enum):
    CAS_RESELECT = "CAS_RESELECT"
    VALIDATE_REBIND = "VALIDATE_REBIND"
    REQUALIFY_ONLY = "REQUALIFY_ONLY"

@dataclass(frozen=True)
class RecoveryDecision:
    strategy: RecoveryStrategy
    standing: str
    reuse_allowed: bool
    reason: str

def decide(strategy: RecoveryStrategy, attempt: RecoveryAttempt, witness: CompatibilityWitness | None) -> RecoveryDecision:
    changed = attempt.base_context.digest != attempt.target_context.digest
    if strategy is RecoveryStrategy.CAS_RESELECT:
        return RecoveryDecision(strategy, "REQUALIFYING", False, "fresh exact reselection required")
    if strategy is RecoveryStrategy.VALIDATE_REBIND:
        if not changed:
            return RecoveryDecision(strategy, "REQUALIFYING", True, "unchanged context")
        if witness is None or witness.result != "PASS":
            raise Refusal("REBIND_WITNESS_REQUIRED", "passing witness required")
        if witness.kind not in {WitnessKind.EXACT, WitnessKind.SEMANTIC_EQUIVALENT}:
            raise Refusal("INSUFFICIENT_REBIND_WITNESS", witness.kind.value)
        return RecoveryDecision(strategy, "REQUALIFYING", True, "equivalence-bound rebind")
    if strategy is RecoveryStrategy.REQUALIFY_ONLY:
        return RecoveryDecision(strategy, "REQUALIFYING", False, "conservative requalification")
    raise Refusal("UNKNOWN_RECOVERY_STRATEGY", str(strategy))
