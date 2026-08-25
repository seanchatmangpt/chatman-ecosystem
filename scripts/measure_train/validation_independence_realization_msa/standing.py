def standing(calibration,model,dependency_states=(),drift_alarm=False,robustness=None):
    deps=set(dependency_states)
    if "FAIL" in deps or "BUILD_BROKEN" in deps:return "BUILD_BROKEN"
    if "BLOCKED" in deps:return "BLOCKED"
    if calibration.state!="CALIBRATED" or model.state!="CALIBRATED" or drift_alarm:return "UNKNOWN"
    if robustness is not None and (robustness.max_overlap>0 or robustness.leave_one_out_flip_rate>0): return "UNKNOWN"
    return "PARTIAL_ALIVE"
