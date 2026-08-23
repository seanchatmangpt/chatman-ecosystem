from .refusal import Refused

def admit_cases(subject, cases, now):
    if now.tzinfo is None or now.utcoffset() is None: raise Refused("REFUSED[NAIVE_NOW]")
    seen=set(); admitted=[]
    for c in cases:
        if c.subject != subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if c.observed_at > now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
        key=(c.estimator.estimator_id,c.case_id)
        if key in seen: raise Refused("REFUSED[DUPLICATE_EVALUATION_CASE]")
        seen.add(key); admitted.append(c)
    return tuple(sorted(admitted))
