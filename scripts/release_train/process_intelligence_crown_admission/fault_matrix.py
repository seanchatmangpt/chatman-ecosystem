from dataclasses import dataclass
from enum import Enum
from .refusal import require

class Fault(str, Enum):
    NODE_DOWN="NODE_DOWN"; PARTITION="PARTITION"; LATENCY="LATENCY"; LOSS="LOSS"
    VERSION_SKEW="VERSION_SKEW"; CERTIFICATE="CERTIFICATE"; AMBIGUOUS_DO="AMBIGUOUS_DO"

REQUIRED=frozenset(Fault)

@dataclass(frozen=True)
class FaultWitness:
    fault: Fault
    refused_or_recovered: bool
    receipt_digest: str | None
    actuation_performed: bool

def require_fault_closure(witnesses):
    by={w.fault:w for w in witnesses}
    require(set(by)==set(REQUIRED), "INCOMPLETE_FAILURE_COURT")
    for fault,w in by.items():
        require(w.refused_or_recovered, "UNHANDLED_FAILURE_MODE", fault.value)
        if fault is Fault.AMBIGUOUS_DO: require(not w.actuation_performed, "AMBIGUOUS_DO_ACTUATED")
        require(not w.actuation_performed or w.receipt_digest is not None, "UNRECEIPTED_ACTUATION")
    return True
