def standing(proofs, conflicts=()):
    if conflicts: return "UNKNOWN"
    if not proofs: return "UNKNOWN"
    results=[]
    for p in proofs:
        if p.strategy=="RESELECT":
            results.append("PENDING")
        else:
            results.append(p.witness.result)
    if "FAIL" in results: return "BUILD_BROKEN"
    if any(x in {"PENDING","UNKNOWN"} for x in results): return "UNKNOWN"
    if set(results)=={"UNSUPPORTED"}: return "UNSUPPORTED"
    if "PASS" in results: return "PARTIAL_ALIVE"
    return "UNKNOWN"
