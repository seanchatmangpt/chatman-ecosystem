def bounded_standing(consensus_result, rail_outcomes=()):
    rails = set(rail_outcomes)
    if "FAIL" in rails:
        return "BUILD_BROKEN"
    if "BLOCKED" in rails:
        return "BLOCKED"
    state = consensus_result["state"]
    if state == "STABLE_CONFIRMED":
        return "PARTIAL_ALIVE"
    if state in {"DIVERGED", "DRIFT_CONFIRMED", "INSUFFICIENT"}:
        return "UNKNOWN"
    return "UNKNOWN"
