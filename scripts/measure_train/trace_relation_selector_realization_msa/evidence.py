from .subject import Refused

def admit_realizations(decision, realizations):
    seen={}
    admitted=[]
    for row in realizations:
        if row.subject != decision.subject:
            raise Refused("REFUSED[FOREIGN_REALIZATION_SUBJECT]")
        if row.decision_id != decision.decision_id:
            raise Refused("REFUSED[FOREIGN_DECISION_REALIZATION]")
        if row.observed_at < decision.decided_at:
            raise Refused("REFUSED[PREDECISION_REALIZATION]")
        key=(row.relation,row.source_id)
        previous=seen.get(key)
        if previous is not None and previous.equivalent != row.equivalent:
            raise Refused("REFUSED[CONTRADICTORY_REALIZATION]")
        seen[key]=row
        admitted.append(row)
    return tuple(sorted(set(admitted)))
