def standing(calibration, dependency_states=(), coverage_ok=True, methodology_ok=True, worst_failure_rate=0.0):
    dependencies = set(dependency_states)
    if "BUILD_BROKEN" in dependencies:
        return "BUILD_BROKEN"
    if "BLOCKED" in dependencies:
        return "BLOCKED"
    if calibration.state != "CALIBRATED" or not coverage_ok or not methodology_ok:
        return "UNKNOWN"
    if worst_failure_rate > 0:
        return "UNKNOWN"
    return "PARTIAL_ALIVE"
