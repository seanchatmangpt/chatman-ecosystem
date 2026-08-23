def standing(*,calibration_state,drifted,dependency_states=(),methodology_complete=False,correspondence=False,failure_complete=False):
    deps=set(dependency_states)
    if "BUILD_BROKEN" in deps or "FAIL" in deps: return "BUILD_BROKEN"
    if "BLOCKED" in deps: return "BLOCKED"
    if calibration_state=="UNSUPPORTED": return "UNSUPPORTED"
    if calibration_state!="CALIBRATED" or drifted or not methodology_complete or not correspondence or not failure_complete:
        return "UNKNOWN"
    return "PARTIAL_ALIVE"
