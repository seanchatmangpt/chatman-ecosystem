from enum import Enum
from dataclasses import dataclass
from .compatibility import CompatibilityKind
from .subject import Refusal
class RecoveryStrategy(str,Enum):
    RESELECT='RESELECT'; REBIND_EQUIVALENT='REBIND_EQUIVALENT'; REQUALIFY_COMPATIBLE='REQUALIFY_COMPATIBLE'
@dataclass(frozen=True)
class RecoveryDecision:
    strategy: RecoveryStrategy
    standing: str
    reason: str

def recover(drift, witness, preferred):
    if drift.value=='CURRENT': return RecoveryDecision(preferred,'PARTIAL_ALIVE','CURRENT_INTENT')
    if preferred is RecoveryStrategy.RESELECT:
        return RecoveryDecision(preferred,'REQUALIFYING','RESELECT_REQUIRED')
    if witness is None: raise Refusal('REFUSED[COMPATIBILITY_WITNESS_REQUIRED]')
    if preferred is RecoveryStrategy.REBIND_EQUIVALENT:
        if witness.kind not in {CompatibilityKind.EXACT,CompatibilityKind.SEMANTIC_EQUIVALENT}:
            raise Refusal('REFUSED[INSUFFICIENT_EQUIVALENCE_WITNESS]')
        return RecoveryDecision(preferred,'REQUALIFYING','EQUIVALENT_REBIND_REQUIRES_VERIFY')
    if preferred is RecoveryStrategy.REQUALIFY_COMPATIBLE:
        return RecoveryDecision(preferred,'REQUALIFYING','COMPATIBLE_REQUALIFICATION_REQUIRED')
    raise Refusal('REFUSED[UNKNOWN_RECOVERY_STRATEGY]')
