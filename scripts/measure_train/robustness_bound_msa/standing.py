def standing(calibrations, dependency_states=()):
    deps=set(dependency_states)
    if "BUILD_BROKEN" in deps or "BLOCKED" in deps: return "BLOCKED"
    states={c.state for c in calibrations}
    if not calibrations or "UNRELIABLE" in states or "INSUFFICIENT" in states: return "UNKNOWN"
    if states=={"UNSUPPORTED"}: return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
