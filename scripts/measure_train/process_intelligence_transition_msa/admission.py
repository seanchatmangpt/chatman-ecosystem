from .subject import Refused

def admit_evidence(epoch, obligations, evidence, now):
    obligation_ids = {o.obligation_id for o in obligations}
    seen = {}
    admitted = []
    for row in evidence:
        if row.epoch != epoch:
            raise Refused("REFUSED[FOREIGN_OR_STALE_SUBJECT]")
        if row.obligation_id not in obligation_ids:
            raise Refused("REFUSED[UNKNOWN_OBLIGATION]")
        if row.observed_at > now:
            raise Refused("REFUSED[FUTURE_EVIDENCE]")
        key = (row.obligation_id, row.source_id)
        previous = seen.get(key)
        if previous is not None and previous.state != row.state:
            raise Refused("REFUSED[CONTRADICTORY_SOURCE_EVIDENCE]")
        seen[key] = row
        admitted.append(row)
    return tuple(sorted(set(admitted)))
