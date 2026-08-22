from collections import defaultdict
from .scope import satisfies_scope
from .subject import Subject, Refusal
from .witness import Witness
from .obligation import Obligation

def admit(subject: Subject, obligations: list[Obligation], witnesses: list[Witness]):
    by_id={o.obligation_id:o for o in obligations}
    if len(by_id)!=len(obligations): raise Refusal("DUPLICATE_OBLIGATION")
    seen=defaultdict(set)
    admitted=[]
    for w in witnesses:
        if w.subject != subject: raise Refusal("FOREIGN_SUBJECT")
        candidates=[o for o in obligations if o.axis==w.axis and satisfies_scope(w.scope,o.scope)]
        for o in candidates:
            key=(o.obligation_id,w.source,w.scope)
            seen[key].add(w.outcome)
            if len(seen[key])>1: raise Refusal("CONTRADICTORY_WITNESS")
        admitted.append(w)
    return tuple(sorted(admitted,key=lambda w:(w.axis.value,w.scope,w.source,w.outcome.value,w.observed_at.isoformat())))
