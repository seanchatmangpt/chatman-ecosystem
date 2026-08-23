def derive(*, blockers=(), failed=False, stale=False, drifted=False, reliable=False, hold=False):
    if blockers: return "BLOCKED"
    if failed: return "BUILD_BROKEN"
    if stale or drifted or not reliable: return "UNKNOWN"
    if hold: return "PARTIAL_ALIVE"
    return "UNKNOWN"
