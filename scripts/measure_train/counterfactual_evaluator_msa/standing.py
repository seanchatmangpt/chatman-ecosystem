def standing(consensus_state, outcomes=(), dependency_standings=()):
    if any(x in {"BUILD_BROKEN","BLOCKED"} for x in dependency_standings): return "BLOCKED"
    if "FAIL" in outcomes: return "BUILD_BROKEN"
    if not outcomes or "PENDING" in outcomes or "UNKNOWN" in outcomes or consensus_state!="COHERENT": return "UNKNOWN"
    if set(outcomes)=={"UNSUPPORTED"}: return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
