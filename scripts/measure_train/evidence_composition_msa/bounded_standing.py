def standing(nodes, calibration, methodology_complete, blocker_cut=()):
    states={n.state for n in nodes}
    if "FAIL" in states: return "BUILD_BROKEN"
    if blocker_cut: return "BLOCKED"
    if "REFUSED" in states or "UNKNOWN" in states: return "UNKNOWN"
    if calibration.state!="CALIBRATED" or not methodology_complete: return "UNKNOWN"
    if states=={"UNSUPPORTED"}: return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
