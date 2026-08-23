def standing(census, drift_alarm=False, regret_values=()):
    deps=set(census.get("dependencies",()))
    if "BUILD_BROKEN" in deps or "FAIL" in deps:
        return "BUILD_BROKEN"
    if "BLOCKED" in deps:
        return "BLOCKED"
    calibration=census["calibration"]
    if calibration.state!="CALIBRATED" or drift_alarm:
        return "UNKNOWN"
    if regret_values and max(regret_values)>0:
        return "PARTIAL_ALIVE"
    return "PARTIAL_ALIVE"
