from .subject import Subject, Refused

def admit(subject: Subject, evidence):
    admitted = []
    by_identity = {}
    for item in evidence:
        if item.subject != subject:
            raise Refused("REFUSED[FOREIGN_SUBJECT]")
        key = (item.kind, item.scope, item.source_id, item.epoch)
        previous = by_identity.get(key)
        if previous and previous.outcome != item.outcome:
            raise Refused("REFUSED[CONTRADICTORY_EVIDENCE]")
        by_identity[key] = item
        admitted.append(item)
    return tuple(sorted(set(admitted)))
