def standing(observations,calibration,methodology_complete,dependency_states=()):
    states={o.state for o in observations}; deps=set(dependency_states)
    if "BUILD_BROKEN" in deps or "FAIL" in states:return "BUILD_BROKEN"
    if "BLOCKED" in deps:return "BLOCKED"
    if "REFUSED" in states or "UNKNOWN" in states:return "UNKNOWN"
    if calibration.state!="CALIBRATED" or not methodology_complete:return "UNKNOWN"
    if states=={"UNSUPPORTED"}:return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
