from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .compatibility import CompatibilityWitness, admits_rebind
from .drift import DriftKind
class RecoveryStrategy(str,Enum):
    RESELECT="RESELECT"; REBIND_EQUIVALENT="REBIND_EQUIVALENT"; REQUALIFY_COMPATIBLE="REQUALIFY_COMPATIBLE"
@dataclass(frozen=True,slots=True)
class RecoveryDecision:
    strategy:RecoveryStrategy; standing:str; reusable:bool; requires_new_proof:bool
def recover(strategy:RecoveryStrategy,drift:DriftKind,witness:CompatibilityWitness|None=None)->RecoveryDecision:
    if drift is DriftKind.EXACT: return RecoveryDecision(strategy,"PARTIAL_ALIVE",True,False)
    if strategy is RecoveryStrategy.RESELECT: return RecoveryDecision(strategy,"REQUALIFYING",False,True)
    if strategy is RecoveryStrategy.REBIND_EQUIVALENT:
        if not admits_rebind(drift,witness): raise ValueError("REFUSED[INSUFFICIENT_EQUIVALENCE_WITNESS]")
        return RecoveryDecision(strategy,"REQUALIFYING",True,True)
    if strategy is RecoveryStrategy.REQUALIFY_COMPATIBLE:
        if witness is None: raise ValueError("REFUSED[COMPATIBILITY_WITNESS_REQUIRED]")
        return RecoveryDecision(strategy,"REQUALIFYING",False,True)
    raise ValueError("REFUSED[UNKNOWN_RECOVERY_STRATEGY]")
