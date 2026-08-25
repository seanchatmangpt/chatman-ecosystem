def standing(*, dependency="PARTIAL_ALIVE", drift=False, calibrated=True, closure=True):
    if dependency in {"BUILD_BROKEN", "BLOCKED"}:
        return dependency
    if drift or not calibrated or not closure:
        return "UNKNOWN"
    return "PARTIAL_ALIVE"
