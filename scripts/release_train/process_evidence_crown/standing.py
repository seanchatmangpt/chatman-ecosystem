from enum import Enum
class Standing(str,Enum): UNKNOWN='UNKNOWN'; PARTIAL_ALIVE='PARTIAL_ALIVE'; ALIVE='ALIVE'; BLOCKED='BLOCKED'; BUILD_BROKEN='BUILD_BROKEN'; UNSUPPORTED='UNSUPPORTED'
def combine(values):
    v=set(values)
    for s in (Standing.BUILD_BROKEN,Standing.BLOCKED,Standing.UNKNOWN,Standing.UNSUPPORTED):
        if s in v: return s
    return Standing.PARTIAL_ALIVE
