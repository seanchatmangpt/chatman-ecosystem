from __future__ import annotations
from enum import IntEnum
from .hysteresis import RegimeState

class Standing(IntEnum):
    BUILD_BROKEN = 0
    BLOCKED = 1
    UNKNOWN = 2
    PARTIAL_ALIVE = 3

def bounded_standing(regime: RegimeState, dependency: Standing, evidence_current: bool) -> Standing:
    if dependency is Standing.BUILD_BROKEN:
        return Standing.BUILD_BROKEN
    if dependency is Standing.BLOCKED:
        return Standing.BLOCKED
    if regime is not RegimeState.STABLE or not evidence_current:
        return Standing.UNKNOWN
    return min(dependency, Standing.PARTIAL_ALIVE)
