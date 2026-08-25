def standing(current_epoch, convergence, blocking_cut=()):
    states={o.state for o in current_epoch.obligations}
    if "FAIL" in states: return "BUILD_BROKEN"
    if "BLOCKED" in states or blocking_cut: return "BLOCKED"
    if convergence.direction in {"OSCILLATING","REGRESSING","STALLED","UNKNOWN"}: return "UNKNOWN"
    if "UNKNOWN" in states or "REFUSED" in states: return "UNKNOWN"
    if states == {"UNSUPPORTED"}: return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
