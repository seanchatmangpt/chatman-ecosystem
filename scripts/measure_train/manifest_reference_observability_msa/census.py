def component_census(components, observations):
    grouped={c.component_id:[] for c in components}
    for row in observations:
        grouped[row.component_id].append(row)
    result=[]
    for c in sorted(components):
        rows=grouped[c.component_id]
        relations={r.relation for r in rows if r.status=="RESOLVED"}
        statuses={r.status for r in rows}
        if "DIVERGED" in relations:
            state="DIVERGED"
        elif "EXACT" in relations:
            state="EXACT"
        elif "ADVANCED" in relations:
            state="ADVANCED"
        elif statuses and statuses <= {"UNSUPPORTED"}:
            state="UNSUPPORTED"
        elif rows:
            state="CENSORED"
        else:
            state="UNKNOWN"
        result.append((c.component_id,c.required,state,len(rows)))
    return tuple(result)
