from .subject import Refused

def admit_observations(subject, observations, now):
    rows=tuple(observations)
    seen={}
    pair=None
    for row in rows:
        if row.subject != subject:
            raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if row.observed_at > now:
            raise Refused("REFUSED[FUTURE_OBSERVATION]")
        key=tuple(sorted((row.left_id,row.right_id)))
        if pair is None:
            pair=key
        elif key != pair:
            raise Refused("REFUSED[MIXED_EVIDENCE_PAIRS]")
        old=seen.get(row.observation_id)
        if old is not None and old != row:
            raise Refused("REFUSED[CONTRADICTORY_DUPLICATE_OBSERVATION]")
        seen[row.observation_id]=row
    return tuple(sorted(seen.values()))
