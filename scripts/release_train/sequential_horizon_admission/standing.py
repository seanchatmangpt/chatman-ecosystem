from .horizon import HorizonState
def standing(state):
    if state is HorizonState.BLOCKED: return "BLOCKED"
    if state in {HorizonState.DRIFTED,HorizonState.STALE,HorizonState.EXHAUSTED}: return "UNKNOWN"
    if state is HorizonState.SATISFIED: return "PARTIAL_ALIVE"
    return "UNKNOWN"
