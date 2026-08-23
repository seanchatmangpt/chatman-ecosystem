def standing(steps,budget_state,calibration_state,dependency_states=()):
    outcomes={s.outcome for s in steps}
    deps=set(dependency_states)
    if "BUILD_BROKEN" in deps or "BLOCKED" in deps:
        return "BLOCKED"
    if "FAIL" in outcomes:
        return "BUILD_BROKEN"
    if budget_state["exhausted"] or calibration_state != "CALIBRATED":
        return "UNKNOWN"
    if not steps or "PENDING" in outcomes or "UNKNOWN" in outcomes:
        return "UNKNOWN"
    if outcomes == {"UNSUPPORTED"}:
        return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
