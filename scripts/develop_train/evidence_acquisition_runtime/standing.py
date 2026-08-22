from enum import Enum
class Standing(str,Enum):
    UNKNOWN='UNKNOWN'; PARTIAL_ALIVE='PARTIAL_ALIVE'; BLOCKED='BLOCKED'; BUILD_BROKEN='BUILD_BROKEN'
def bounded_standing(*,selected_count,dependency_states):
    if 'BUILD_BROKEN' in dependency_states: return Standing.BUILD_BROKEN
    if 'BLOCKED' in dependency_states: return Standing.BLOCKED
    return Standing.PARTIAL_ALIVE if selected_count else Standing.UNKNOWN
