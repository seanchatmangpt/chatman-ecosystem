from .subject import Refused
from .provenance import validate_acyclic

def admit(subject, observations, edges, now):
    if now.tzinfo is None or now.utcoffset() is None:
        raise Refused("REFUSED[NAIVE_NOW]")
    seen={}
    admitted=[]
    for o in observations:
        if o.subject != subject:
            raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if o.observed_at > now:
            raise Refused("REFUSED[FUTURE_EVIDENCE]")
        prior=seen.get(o.evidence_id)
        if prior and prior != o:
            raise Refused("REFUSED[CONTRADICTORY_EVIDENCE_ID]")
        seen[o.evidence_id]=o
        admitted.append(o)
    validate_acyclic(admitted,edges)
    return tuple(sorted(set(admitted)))
