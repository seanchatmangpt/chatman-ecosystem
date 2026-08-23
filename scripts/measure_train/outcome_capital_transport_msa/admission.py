from .subject import Refused
def admit(subject, observations, now):
    seen={}
    out=[]
    for o in observations:
        if o.subject != subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if o.observed_at > now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
        old=seen.get(o.evidence_id)
        if old is not None:
            if old != o: raise Refused("REFUSED[CONTRADICTORY_DUPLICATE_EVIDENCE]")
            raise Refused("REFUSED[DUPLICATE_EVIDENCE]")
        seen[o.evidence_id]=o; out.append(o)
    return tuple(sorted(out))
