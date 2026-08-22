from .contradiction import contradictions

def qualify(*, movement_material, ci_outcomes, runtime_standing, stale, contradictions_rows):
    if stale: return "UNKNOWN"
    if contradictions(contradictions_rows): return "UNKNOWN"
    if "FAIL" in ci_outcomes or runtime_standing=="BUILD_BROKEN": return "BUILD_BROKEN"
    if not movement_material and not ci_outcomes: return "UNKNOWN"
    if ci_outcomes and all(x=="UNSUPPORTED" for x in ci_outcomes): return "UNSUPPORTED"
    return "PARTIAL_ALIVE"
