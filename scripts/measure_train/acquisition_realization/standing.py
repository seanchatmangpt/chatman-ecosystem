def standing(calibration, outcomes, dependency_states=()):
    if any(x in {"BUILD_BROKEN","BLOCKED"} for x in dependency_states):
        return "BLOCKED"
    states={o.outcome for o in outcomes}
    if "FAIL" in states:
        return "BUILD_BROKEN"
    if "PENDING" in states or "UNKNOWN" in states or not outcomes:
        return "UNKNOWN"
    if states=={"UNSUPPORTED"}:
        return "UNSUPPORTED"
    if calibration.calibration_state!="CALIBRATED":
        return "UNKNOWN"
    return "PARTIAL_ALIVE"
