from enum import Enum

class Standing(str, Enum):
    UNKNOWN='UNKNOWN'; PARTIAL_ALIVE='PARTIAL_ALIVE'; BLOCKED='BLOCKED'; BUILD_BROKEN='BUILD_BROKEN'; UNSUPPORTED='UNSUPPORTED'

def aggregate(outcomes: tuple[str,...]) -> Standing:
    vals=set(outcomes)
    if 'FAIL' in vals: return Standing.BUILD_BROKEN
    if 'BLOCKED' in vals: return Standing.BLOCKED
    if vals and vals <= {'UNSUPPORTED'}: return Standing.UNSUPPORTED
    if 'PENDING' in vals or 'UNKNOWN' in vals or not vals: return Standing.UNKNOWN
    return Standing.PARTIAL_ALIVE
