def standing(calibrations, dependency_states=()):
    deps=set(dependency_states)
    if "FAIL" in deps or "BUILD_BROKEN" in deps:
        return "BUILD_BROKEN"
    if "BLOCKED" in deps:
        return "BLOCKED"
    states={c.state for c in calibrations}
    if not calibrations or "INSUFFICIENT" in states or "UNRELIABLE" in states:
        return "UNKNOWN"
    if states=={"CALIBRATED"}:
        return "PARTIAL_ALIVE"
    return "UNKNOWN"
