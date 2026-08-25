from .refusal import Refused
def admit(subject, observations, now):
    seen=set(); out=[]
    for o in observations:
        if o.projection.subject != subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if o.observed_at > now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
        if o.projection.projection_id in seen: raise Refused("REFUSED[DUPLICATE_PROJECTION]")
        seen.add(o.projection.projection_id); out.append(o)
    return tuple(sorted(out,key=lambda x:x.projection.projection_id))
