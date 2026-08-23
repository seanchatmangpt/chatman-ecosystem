from .errors import Refused

def admit(subject,policy,observations,now):
    seen={}; admitted=[]
    for row in observations:
        if row.subject!=subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if (row.policy_id,row.policy_generation,row.policy_digest)!=(policy.policy_id,policy.generation,policy.digest): raise Refused("REFUSED[STALE_OR_FOREIGN_POLICY]")
        if row.observed_at>now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
        previous=seen.get(row.decision_id)
        if previous is not None and previous!=row: raise Refused("REFUSED[CONTRADICTORY_DECISION_ID]")
        seen[row.decision_id]=row; admitted.append(row)
    return tuple(sorted(set(admitted)))
