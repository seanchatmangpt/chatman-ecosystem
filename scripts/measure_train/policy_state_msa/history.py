from .subject import Refused
from .invariants import check_transition

def admit_history(subject, transitions):
    rows=tuple(sorted(transitions,key=lambda x:(x.completed_at,x.event_id)))
    seen=set()
    for t in rows:
        if t.before.subject != subject: raise Refused("REFUSED[FOREIGN_HISTORY_SUBJECT]")
        if t.event_id in seen: raise Refused("REFUSED[DUPLICATE_EVENT_ID]")
        seen.add(t.event_id)
        verdict=check_transition(t)
        if t.outcome=="COMMITTED" and verdict!="PASS": raise Refused("REFUSED[INVALID_COMMITTED_TRANSITION]:"+verdict)
    return rows
