def compute(*states, drifted=False, calibrated=True):
    if "BUILD_BROKEN" in states: return "BUILD_BROKEN"
    if "BLOCKED" in states: return "BLOCKED"
    if drifted or not calibrated or "UNKNOWN" in states: return "UNKNOWN"
    return "PARTIAL_ALIVE"
