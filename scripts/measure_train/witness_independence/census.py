from .clusters import correlated_clusters

def cluster_census(observations, edges=()):
    rows=[]
    for cluster in correlated_clusters(observations,edges):
        outcomes={o.outcome for o in cluster}
        scopes={o.scope for o in cluster}
        if "FAIL" in outcomes:
            state="FAIL"
        elif "PASS" in outcomes and len(outcomes)>1:
            state="CONTRADICTED"
        elif "PENDING" in outcomes or "UNKNOWN" in outcomes:
            state="UNKNOWN"
        elif outcomes=={"UNSUPPORTED"}:
            state="UNSUPPORTED"
        elif outcomes=={"PASS"}:
            state="PASS"
        else:
            state="UNKNOWN"
        rows.append({
            "cluster_id": min(o.evidence_id for o in cluster),
            "members": tuple(sorted(o.evidence_id for o in cluster)),
            "scopes": tuple(sorted(scopes)),
            "state": state,
        })
    return tuple(rows)
