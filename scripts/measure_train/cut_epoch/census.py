def cut_census(observations):
    rows={}
    for repo,outcome in observations:
        rows.setdefault(repo,set()).add(outcome)
    result=[]
    for repo,outcomes in sorted(rows.items()):
        if "FAIL" in outcomes: state="FAIL"
        elif "PENDING" in outcomes or "UNKNOWN" in outcomes: state="UNKNOWN"
        elif outcomes=={"UNSUPPORTED"}: state="UNSUPPORTED"
        elif outcomes=={"PASS"}: state="PASS"
        else: state="CONTRADICTED"
        result.append((repo,state))
    return tuple(result)
def standing(rows):
    if not rows:return "UNKNOWN"
    states={s for _,s in rows}
    if "FAIL" in states:return "BUILD_BROKEN"
    if "UNKNOWN" in states or "CONTRADICTED" in states:return "UNKNOWN"
    if states=={"UNSUPPORTED"}:return "UNSUPPORTED"
    if "PASS" in states:return "PARTIAL_ALIVE"
    return "UNKNOWN"
