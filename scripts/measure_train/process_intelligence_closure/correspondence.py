from collections import defaultdict
from .subject import Refused

def admit_correspondence(subject,evidence):
    by_key={}; admitted=[]
    for e in evidence:
        if e.subject!=subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        k=(e.rail,e.engine,e.evidence_id)
        old=by_key.get(k)
        if old and (old.outcome!=e.outcome or old.semantic_digest!=e.semantic_digest): raise Refused("REFUSED[CONTRADICTORY_RAIL_EVIDENCE]")
        by_key[k]=e; admitted.append(e)
    return tuple(sorted(set(admitted)))

def rail_equivalence(evidence):
    digests=defaultdict(set); outcomes=defaultdict(set)
    for e in evidence:
        digests[e.rail].add(e.semantic_digest); outcomes[e.rail].add(e.outcome)
    divergent=tuple(sorted(r for r,v in digests.items() if len(v)>1))
    contradictory=tuple(sorted(r for r,v in outcomes.items() if "PASS" in v and "FAIL" in v))
    return {"divergent":divergent,"contradictory":contradictory}
