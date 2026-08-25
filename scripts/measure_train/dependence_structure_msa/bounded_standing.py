def standing(verdicts, calibration, dependency_states=()):
    deps=set(dependency_states)
    if "BUILD_BROKEN" in deps or "FAIL" in deps:
        return "BUILD_BROKEN"
    if "BLOCKED" in deps:
        return "BLOCKED"
    if calibration.state!="CALIBRATED":
        return "UNKNOWN"
    states=set(verdicts)
    if "INSUFFICIENT" in states or "UNKNOWN" in states:
        return "UNKNOWN"
    if not states:
        return "UNKNOWN"
    return "PARTIAL_ALIVE"
