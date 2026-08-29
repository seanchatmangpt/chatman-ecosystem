def bounded_standing(witnesses, admissions, decision, independent_count, required_clusters, blockers):
    if blockers: return "BLOCKED"
    if any(w.outcome=="FAIL" for w in witnesses): return "BUILD_BROKEN"
    if independent_count < required_clusters: return "UNKNOWN"
    if not all(a["admitted"] for a in admissions): return "UNKNOWN"
    if decision.decision!="ACCEPT_BOUNDED": return "UNKNOWN"
    return "PARTIAL_ALIVE"
