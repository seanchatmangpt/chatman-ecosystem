def standing(calibration,capital,dependency_states=()):
    ds=set(dependency_states)
    if "BUILD_BROKEN" in ds or "FAIL" in ds: return "BUILD_BROKEN"
    if "BLOCKED" in ds: return "BLOCKED"
    if calibration.state!="CALIBRATED" or capital.effective_n<2: return "UNKNOWN"
    return "PARTIAL_ALIVE"
