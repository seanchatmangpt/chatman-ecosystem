def standing(model, overlap_fraction, ess, calibration_gap, simpson, dependency_states=()):
    deps=set(dependency_states)
    if "BUILD_BROKEN" in deps:return "BUILD_BROKEN"
    if "BLOCKED" in deps:return "BLOCKED"
    if not model.calibrated or overlap_fraction<1 or ess<2 or calibration_gap>0.25 or simpson:return "UNKNOWN"
    return "PARTIAL_ALIVE"
