from .refusal import Refused
def admit(subject, observations, now):
    seen={}; admitted=[]
    for row in observations:
        if row.subject != subject: raise Refused("REFUSED[FOREIGN_OR_STALE_SUBJECT]")
        if row.observed_at > now: raise Refused("REFUSED[FUTURE_OBSERVATION]")
        old=seen.get(row.observation_id)
        if old is not None and old != row: raise Refused("REFUSED[CONTRADICTORY_DUPLICATE_OBSERVATION]")
        seen[row.observation_id]=row; admitted.append(row)
    return tuple(sorted(set(admitted)))
