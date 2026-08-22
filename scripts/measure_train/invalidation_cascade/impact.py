def direct_impact(bindings, event):
    affected=[]
    for b in bindings:
        if b.producer != event.producer:
            continue
        reason={
            "NEW_HEAD":"PRODUCER_HEAD_MOVED",
            "NEW_RECEIPT":"PRODUCER_RECEIPT_SUPERSEDED",
            "SCHEMA_CHANGE":"PRODUCER_SCHEMA_DRIFT",
            "EXPIRED":"EVIDENCE_EXPIRED",
            "BUILD_BROKEN":"PRODUCER_BUILD_BROKEN",
            "BLOCKED":"PRODUCER_BLOCKED",
            "RECOVERED":"PRODUCER_RECOVERED",
        }[event.kind]
        affected.append((b.binding_id,reason))
    return tuple(sorted(affected))
