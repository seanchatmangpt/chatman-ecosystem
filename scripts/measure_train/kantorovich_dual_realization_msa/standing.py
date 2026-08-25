def standing(calibration, dependencies=()):
    deps=set(dependencies)
    if "FAIL" in deps or "BUILD_BROKEN" in deps:return "BUILD_BROKEN"
    if "BLOCKED" in deps:return "BLOCKED"
    if calibration.state!="CALIBRATED":return "UNKNOWN"
    return "PARTIAL_ALIVE"
