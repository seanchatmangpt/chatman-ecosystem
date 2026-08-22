from dataclasses import dataclass
from enum import Enum
from .coverage import Coverage, CoverageState
from .obligation import Requiredness

class Standing(str, Enum): UNKNOWN="UNKNOWN"; PARTIAL_ALIVE="PARTIAL_ALIVE"; BLOCKED="BLOCKED"; BUILD_BROKEN="BUILD_BROKEN"; UNSUPPORTED="UNSUPPORTED"

@dataclass(frozen=True)
class Coherence:
    standing: Standing
    unsatisfied: tuple[str,...]
    satisfied: tuple[str,...]

def evaluate(rows: tuple[Coverage,...]) -> Coherence:
    required=[r for r in rows if r.obligation.requiredness==Requiredness.REQUIRED]
    if any(r.state==CoverageState.FAILED for r in required): standing=Standing.BUILD_BROKEN
    elif any(r.state==CoverageState.PENDING for r in required): standing=Standing.UNKNOWN
    elif any(r.state==CoverageState.UNKNOWN for r in required): standing=Standing.UNKNOWN
    elif required and all(r.state==CoverageState.UNSUPPORTED for r in required): standing=Standing.UNSUPPORTED
    elif any(r.state==CoverageState.UNSUPPORTED for r in required): standing=Standing.BLOCKED
    elif required and all(r.state==CoverageState.SATISFIED for r in required): standing=Standing.PARTIAL_ALIVE
    else: standing=Standing.UNKNOWN
    sat=tuple(r.obligation.obligation_id for r in required if r.state==CoverageState.SATISFIED)
    unsat=tuple(r.obligation.obligation_id for r in required if r.state!=CoverageState.SATISFIED)
    return Coherence(standing,unsat,sat)
