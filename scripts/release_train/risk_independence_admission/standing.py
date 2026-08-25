from enum import Enum
class Standing(str,Enum): UNKNOWN='UNKNOWN'; PARTIAL_ALIVE='PARTIAL_ALIVE'; ALIVE='ALIVE'; BLOCKED='BLOCKED'; BUILD_BROKEN='BUILD_BROKEN'; UNSUPPORTED='UNSUPPORTED'
def compute(*,failed=False,blocked=False,deferred=False,qualified=False):
    if failed:return Standing.BUILD_BROKEN
    if blocked:return Standing.BLOCKED
    if deferred:return Standing.UNKNOWN
    return Standing.PARTIAL_ALIVE if qualified else Standing.UNKNOWN
