def standing(census, propagated=None):
    states = dict(propagated or ((row[0], row[3]) for row in census))
    required_ids = [row[0] for row in census if row[2]]
    required_states = {states.get(oid, "UNKNOWN") for oid in required_ids}
    if "BLOCKED" in required_states:
        return "BLOCKED"
    if "FAIL" in required_states or "REFUSED" in required_states:
        return "BUILD_BROKEN"
    if not required_ids or "UNKNOWN" in required_states:
        return "UNKNOWN"
    if required_states == {"UNSUPPORTED"}:
        return "UNSUPPORTED"
    if required_states <= {"PASS","UNSUPPORTED"} and "PASS" in required_states:
        return "PARTIAL_ALIVE"
    return "UNKNOWN"
