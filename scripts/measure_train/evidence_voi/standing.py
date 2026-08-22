def bounded_standing(selected, dependency_standing="PARTIAL_ALIVE"):
    if dependency_standing in {"BUILD_BROKEN","BLOCKED"}: return "BLOCKED"
    if dependency_standing in {"UNKNOWN","UNSUPPORTED"}: return "UNKNOWN"
    if not selected: return "UNKNOWN"
    return "PARTIAL_ALIVE"
