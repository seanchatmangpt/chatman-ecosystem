def standing(selected_candidate, contradictions_found=(), dependency_states=()):
    if contradictions_found:
        return "UNKNOWN"
    if any(state in {"BUILD_BROKEN", "BLOCKED"} for state in dependency_states):
        return "BLOCKED"
    if any(state == "UNKNOWN" for state in dependency_states):
        return "UNKNOWN"
    if selected_candidate is None:
        return "UNKNOWN"
    if not selected_candidate.complete:
        return "UNKNOWN"
    return "PARTIAL_ALIVE"
