def bounded_standing(fusion_state, dependency_standings=()):
    if any(s in {"BUILD_BROKEN","BLOCKED"} for s in dependency_standings): return "BLOCKED"
    if fusion_state!="COHERENT": return "UNKNOWN"
    if any(s=="UNKNOWN" for s in dependency_standings): return "UNKNOWN"
    return "PARTIAL_ALIVE"
