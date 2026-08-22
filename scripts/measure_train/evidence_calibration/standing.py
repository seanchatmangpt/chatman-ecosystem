def standing(witnesses, undercalibrated, seq, min_independent_clusters):
    if any(w.outcome=="FAIL" for w in witnesses): return "BUILD_BROKEN"
    if undercalibrated: return "UNKNOWN"
    clusters={w.cluster_id for w in witnesses if w.outcome=="PASS"}
    if any(w.outcome in {"PENDING","UNKNOWN"} for w in witnesses): return "UNKNOWN"
    if witnesses and all(w.outcome=="UNSUPPORTED" for w in witnesses): return "UNSUPPORTED"
    if len(clusters) < min_independent_clusters: return "UNKNOWN"
    if seq.decision=="ACCEPT_BOUNDED": return "PARTIAL_ALIVE"
    if seq.decision=="REJECT": return "BUILD_BROKEN"
    return "UNKNOWN"
