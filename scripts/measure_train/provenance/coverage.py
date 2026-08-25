def provenance_coverage(claims, edges):
    ids={c.evidence_id for c in claims}
    linked={e.child_id for e in edges}|{e.parent_id for e in edges}
    missing=tuple(sorted(ids-linked))
    outcomes={c.outcome for c in claims}
    if not claims: standing="UNKNOWN"
    elif "FAIL" in outcomes: standing="BUILD_BROKEN"
    elif "PENDING" in outcomes or "UNKNOWN" in outcomes or missing: standing="UNKNOWN"
    elif outcomes=={"UNSUPPORTED"}: standing="UNSUPPORTED"
    else: standing="PARTIAL_ALIVE"
    return {"standing":standing,"missing_provenance":missing}
