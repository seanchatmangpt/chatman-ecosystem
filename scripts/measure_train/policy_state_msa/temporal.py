def monitor_trace(transitions):
    violations=[]
    for t in transitions:
        if t.outcome=="COMMITTED" and (t.after is None or t.after.revision!=t.before.revision+1): violations.append((t.event_id,"G(COMMIT->NEXT_REVISION)"))
        stale=t.expected_revision!=t.before.revision or t.expected_digest!=t.before.digest
        if stale and t.outcome=="COMMITTED": violations.append((t.event_id,"G(STALE_TOKEN->REFUSED)"))
    return tuple(sorted(violations))
