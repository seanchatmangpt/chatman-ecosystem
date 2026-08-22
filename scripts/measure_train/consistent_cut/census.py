def census(observations):
    rows={}
    for obs in observations:
        key=(obs.producer_epoch.subject.repo, obs.scope)
        rows.setdefault(key,set()).add(obs.outcome)
    result=[]
    for (repo,scope), outcomes in sorted(rows.items()):
        if "FAIL" in outcomes:
            state="FAIL"
        elif "PENDING" in outcomes or "UNKNOWN" in outcomes:
            state="UNKNOWN"
        elif outcomes=={"UNSUPPORTED"}:
            state="UNSUPPORTED"
        elif outcomes=={"PASS"}:
            state="PASS"
        else:
            state="CONTRADICTED"
        result.append((repo,scope,state))
    return tuple(result)
