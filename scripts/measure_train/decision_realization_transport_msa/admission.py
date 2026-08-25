from .errors import Refused
def admit(subject, observations, now):
    seen={}
    out=[]
    for o in observations:
        if o.subject!=subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if o.observed_at>now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
        if not o.observed: raise Refused("REFUSED[UNOBSERVED_OUTCOME]")
        old=seen.get(o.observation_id)
        if old is not None and old!=o: raise Refused("REFUSED[CONTRADICTORY_DUPLICATE]")
        seen[o.observation_id]=o; out.append(o)
    return tuple(sorted(set(out)))
