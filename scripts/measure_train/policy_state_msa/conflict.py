def classify_conflicts(transitions):
    rows=[]
    for t in transitions:
        if t.expected_revision!=t.before.revision or t.expected_digest!=t.before.digest: rows.append((t.event_id,"STALE_WRITER"))
    by_token={}
    for t in transitions: by_token.setdefault((t.expected_revision,t.expected_digest),[]).append(t)
    for group in by_token.values():
        commits=[t for t in group if t.outcome=="COMMITTED"]
        if len(commits)>1: rows.append((commits[-1].event_id,"LOST_UPDATE"))
    digests={}
    for t in transitions:
        digests.setdefault(t.before.payload_digest,t.before.revision)
        if t.after:
            old=digests.get(t.after.payload_digest)
            if old is not None and old!=t.after.revision: rows.append((t.event_id,"ABA_VALUE_RECURRENCE"))
            digests[t.after.payload_digest]=t.after.revision
    return tuple(sorted(set(rows)))
