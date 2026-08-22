from .contradiction import contradictions

def census(consumers, epoch, witnesses):
    conflicts=contradictions(witnesses)
    rows=[]
    for consumer in sorted(consumers):
        ws=[w for w in witnesses if w.consumer==consumer and w.producer==epoch.producer and w.generation==epoch.generation and w.event_id==epoch.event_id]
        kinds={w.kind for w in ws}
        terminal=[w for w in ws if w.kind in {"DISCHARGE","RECOVERY"}]
        if conflicts and any(c[0]==consumer.repo and c[1]==consumer.sha for c in conflicts): state="CONTRADICTED"
        elif "DELIVERY" not in kinds: state="PENDING_DELIVERY"
        elif "ACKNOWLEDGEMENT" not in kinds: state="PENDING_ACK"
        elif not terminal: state="PENDING_DISCHARGE"
        elif any(w.outcome=="BLOCKED" for w in terminal): state="BLOCKED"
        elif terminal and all(w.outcome=="UNSUPPORTED" for w in terminal): state="UNSUPPORTED"
        elif any(w.outcome=="REQUALIFIED" for w in terminal): state="REQUALIFIED"
        else: state="UNKNOWN"
        rows.append((consumer.repo,consumer.sha,state))
    return tuple(rows)
