from .subject import Subject, Refused

def admit_claims(subject: Subject, claims):
    seen={}
    admitted=[]
    for c in claims:
        if c.subject != subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        key=(c.source.kind,c.source.locator,c.evidence_id)
        old=seen.get(key)
        if old and old.outcome != c.outcome: raise Refused("REFUSED[CONTRADICTORY_SOURCE_CLAIM]")
        seen[key]=c
        admitted.append(c)
    return tuple(sorted(set(admitted)))
