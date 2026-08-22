from __future__ import annotations
from dataclasses import dataclass
from .witness import CompatibilityWitness, WitnessKind
from .subject import Refusal
@dataclass(frozen=True)
class RecoveryDecision:
    strategy: str
    standing: str
    reuses_prior_selection: bool

def decide(strategy: str, witness: CompatibilityWitness|None) -> RecoveryDecision:
    if strategy=="CAS_RESELECT": return RecoveryDecision(strategy,"REQUALIFYING",False)
    if strategy=="VALIDATE_REBIND":
        if witness is None or not witness.passed or witness.kind not in {WitnessKind.EXACT,WitnessKind.SEMANTIC_EQUIVALENT}: raise Refusal("REFUSED[REBIND_REQUIRES_EQUIVALENCE]")
        return RecoveryDecision(strategy,"REQUALIFYING",True)
    if strategy=="REQUALIFY_ONLY": return RecoveryDecision(strategy,"REQUALIFYING",False)
    raise Refusal("REFUSED[UNKNOWN_RECOVERY_STRATEGY]")
