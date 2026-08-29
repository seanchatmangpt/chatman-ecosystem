from enum import Enum
from .obligations import ClosureCensus
from .rail_evidence import Outcome

class Standing(str, Enum):
    UNKNOWN="UNKNOWN"; PARTIAL_ALIVE="PARTIAL_ALIVE"; ALIVE="ALIVE"
    BLOCKED="BLOCKED"; BUILD_BROKEN="BUILD_BROKEN"; UNSUPPORTED="UNSUPPORTED"

def compute(census: ClosureCensus, rail_outcomes=(), blockers=(), crown_mode=False):
    if census.failed or any(x is Outcome.FAIL for x in rail_outcomes):
        return Standing.BUILD_BROKEN
    if blockers:
        return Standing.BLOCKED
    if any(x is Outcome.PENDING or x is Outcome.UNKNOWN for x in rail_outcomes):
        return Standing.UNKNOWN
    if census.missing:
        return Standing.UNKNOWN
    if rail_outcomes and all(x is Outcome.UNSUPPORTED for x in rail_outcomes):
        return Standing.UNSUPPORTED
    return Standing.ALIVE if crown_mode else Standing.PARTIAL_ALIVE
