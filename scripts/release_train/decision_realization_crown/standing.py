def compute(*,blockers=(),drift=False,calibration_ok=False,global_ok=False):
    if blockers: return "BLOCKED"
    if drift or not calibration_ok: return "UNKNOWN"
    if not global_ok: return "PARTIAL_ALIVE"
    return "PARTIAL_ALIVE"
