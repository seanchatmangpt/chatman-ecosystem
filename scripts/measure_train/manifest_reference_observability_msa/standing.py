def standing(census, propagated=None):
    states=dict(propagated or ((r[0],r[2]) for r in census))
    required=[r[0] for r in census if r[1]]
    vals={states.get(x,"UNKNOWN") for x in required}
    if "DIVERGED" in vals:
        return "BUILD_BROKEN"
    if "BLOCKED" in vals:
        return "BLOCKED"
    if "CENSORED" in vals:
        return "BLOCKED"
    if "UNKNOWN" in vals:
        return "UNKNOWN"
    if vals=={"UNSUPPORTED"}:
        return "UNSUPPORTED"
    if vals <= {"EXACT","ADVANCED","UNSUPPORTED"} and "EXACT" in vals:
        return "PARTIAL_ALIVE"
    return "UNKNOWN"
