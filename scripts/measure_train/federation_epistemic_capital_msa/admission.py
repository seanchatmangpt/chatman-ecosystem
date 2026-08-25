from .refusal import Refused
def admit(subject,rows,now):
    rows=tuple(rows); seen={}; latest={}
    for r in rows:
        if r.subject!=subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if r.observed_at>now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
        k=(r.transport.transport_id,r.trial_id)
        if k in seen and seen[k]!=r: raise Refused("REFUSED[CONTRADICTORY_DUPLICATE]")
        seen[k]=r; latest[r.transport.transport_id]=max(latest.get(r.transport.transport_id,-1),r.transport.generation)
    return tuple(sorted(set(r for r in rows if r.transport.generation==latest[r.transport.transport_id])))
