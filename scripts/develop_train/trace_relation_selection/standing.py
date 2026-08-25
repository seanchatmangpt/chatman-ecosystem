from enum import Enum

class Standing(str, Enum):
    UNKNOWN = "UNKNOWN"
    PARTIAL_ALIVE = "PARTIAL_ALIVE"
    BUILD_BROKEN = "BUILD_BROKEN"
    BLOCKED = "BLOCKED"

def classify(*, admitted_count: int, hard_failure: bool = False, blocked: bool = False) -> Standing:
    if hard_failure:
        return Standing.BUILD_BROKEN
    if blocked:
        return Standing.BLOCKED
    if admitted_count <= 0:
        return Standing.UNKNOWN
    return Standing.PARTIAL_ALIVE
