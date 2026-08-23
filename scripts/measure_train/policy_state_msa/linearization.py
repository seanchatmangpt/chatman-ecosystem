from .subject import Refused

def cas_linearization(transitions):
    committed=[t for t in transitions if t.outcome=="COMMITTED"]
    ordered=sorted(committed,key=lambda t:(t.after.revision,t.completed_at,t.event_id))
    for index,t in enumerate(ordered):
        if index and t.before != ordered[index-1].after: raise Refused("REFUSED[NONLINEAR_COMMIT_CHAIN]")
    for a in transitions:
        for b in transitions:
            if a.event_id==b.event_id: continue
            if a.completed_at < b.issued_at and a.outcome==b.outcome=="COMMITTED" and a.after.revision >= b.after.revision:
                raise Refused("REFUSED[REALTIME_ORDER_VIOLATION]")
    return tuple(t.event_id for t in ordered)
