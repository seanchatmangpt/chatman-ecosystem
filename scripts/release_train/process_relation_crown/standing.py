from enum import Enum
class Standing(str,Enum): UNKNOWN="UNKNOWN"; PARTIAL_ALIVE="PARTIAL_ALIVE"; BUILD_BROKEN="BUILD_BROKEN"; BLOCKED="BLOCKED"
def compute(*,rail_failure=False,blockers=(),calibrated=False,global_proof=False):
    if rail_failure: return Standing.BUILD_BROKEN
    if blockers: return Standing.BLOCKED
    if not calibrated: return Standing.UNKNOWN
    return Standing.PARTIAL_ALIVE
