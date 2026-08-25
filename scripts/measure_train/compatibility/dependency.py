def propagate(standing, dependencies):
    vals=set(dependencies)
    if "BUILD_BROKEN" in vals: return "BLOCKED"
    if "BLOCKED" in vals: return "BLOCKED"
    if "UNKNOWN" in vals and standing=="PARTIAL_ALIVE": return "UNKNOWN"
    return standing
