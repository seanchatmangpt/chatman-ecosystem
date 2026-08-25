from .subject import Refused

def bounded_standing(outcomes, drift_state, dependency_standings=()):
    if any(x in {"BUILD_BROKEN","BLOCKED"} for x in dependency_standings): return "BLOCKED"
    if drift_state in {"DRIFT","INSUFFICIENT","UNKNOWN"}: return "UNKNOWN"
    outcomes=set(outcomes)
    if not outcomes: return "UNKNOWN"
    if "FAIL" in outcomes: return "BUILD_BROKEN"
    if "PENDING" in outcomes or "UNKNOWN" in outcomes: return "UNKNOWN"
    if outcomes=={"UNSUPPORTED"}: return "UNSUPPORTED"
    if "PASS" in outcomes: return "PARTIAL_ALIVE"
    raise Refused("REFUSED[INVALID_STANDING_VECTOR]")
