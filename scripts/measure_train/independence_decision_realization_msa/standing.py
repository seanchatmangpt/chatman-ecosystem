def standing(census_result,drifted=False,dependency_states=(),max_error_upper=0.5):
    deps=set(dependency_states)
    if "BUILD_BROKEN" in deps: return "BUILD_BROKEN"
    if "BLOCKED" in deps: return "BLOCKED"
    if "REFUSED" in deps: return "UNKNOWN"
    if census_result["support"]==0: return "UNKNOWN"
    if census_result["calibration_state"]!="CALIBRATED": return "UNKNOWN"
    if drifted: return "UNKNOWN"
    if census_result["error_wilson_upper"]>max_error_upper: return "UNKNOWN"
    return "PARTIAL_ALIVE"
