def combine(states, blockers=()):
    s=set(states)
    if blockers or "BLOCKED" in s: return "BLOCKED"
    if "BUILD_BROKEN" in s: return "BUILD_BROKEN"
    if "UNKNOWN" in s or not s: return "UNKNOWN"
    if "UNSUPPORTED" in s and s=={"UNSUPPORTED"}: return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
