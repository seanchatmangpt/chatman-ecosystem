def standing(outcomes):
    states=set(outcomes)
    if not states: return "UNKNOWN"
    if "FAIL" in states: return "BUILD_BROKEN"
    if "PENDING" in states or "UNKNOWN" in states or "CONTRADICTED" in states: return "UNKNOWN"
    if states=={"UNSUPPORTED"}: return "UNSUPPORTED"
    if "PASS" in states: return "PARTIAL_ALIVE"
    return "UNKNOWN"
