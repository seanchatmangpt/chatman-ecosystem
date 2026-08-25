def standing(capability_state, calibration_state, effective_support, worst_failure, dependency_states=()):
    dependencies = set(dependency_states)
    if "BUILD_BROKEN" in dependencies:
        return "BUILD_BROKEN"
    if "BLOCKED" in dependencies:
        return "BLOCKED"
    if capability_state == "INCAPABLE" or calibration_state == "UNRELIABLE":
        return "UNSUPPORTED"
    if capability_state != "CAPABLE" or calibration_state != "CALIBRATED" or effective_support < 2:
        return "UNKNOWN"
    if worst_failure > 0:
        return "UNKNOWN"
    return "PARTIAL_ALIVE"
