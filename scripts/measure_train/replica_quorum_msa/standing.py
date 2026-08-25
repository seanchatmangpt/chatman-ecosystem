def bounded_standing(quorum,calibration_state,violations=(),dependency_standings=()):
    if any(x in {"BUILD_BROKEN","BLOCKED"} for x in dependency_standings): return "BLOCKED"
    if quorum["state"] in {"AMBIGUOUS","CONCURRENT"} or violations:return "UNKNOWN"
    if quorum["state"]=="INSUFFICIENT" or calibration_state!="CALIBRATED":return "UNKNOWN"
    return "PARTIAL_ALIVE"
