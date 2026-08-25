def standing(census, dependencies=()):
    data=dict(census)
    if any(x in {"BUILD_BROKEN","BLOCKED"} for x in dependencies): return "BLOCKED"
    if data.get("calibration")!="CALIBRATED" or data.get("drifted") or not data.get("within_budget"): return "UNKNOWN"
    if data.get("realized_gain_bits",0.0)<=0: return "UNKNOWN"
    if data.get("submodularity_ratio",0.0)<0.25: return "UNKNOWN"
    return "PARTIAL_ALIVE"
