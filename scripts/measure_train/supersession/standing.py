def standing(current_evidence, contradictions_found=()):
    if contradictions_found:
        return "UNKNOWN"
    if not current_evidence:
        return "UNKNOWN"
    outcomes = {item.outcome for item in current_evidence}
    if "FAIL" in outcomes:
        return "BUILD_BROKEN"
    if "PENDING" in outcomes or "UNKNOWN" in outcomes:
        return "UNKNOWN"
    if outcomes == {"UNSUPPORTED"}:
        return "UNSUPPORTED"
    if outcomes <= {"PASS", "UNSUPPORTED"} and "PASS" in outcomes:
        return "PARTIAL_ALIVE"
    return "UNKNOWN"
