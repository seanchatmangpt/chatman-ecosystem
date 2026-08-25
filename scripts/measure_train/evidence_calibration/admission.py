from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused
@dataclass(frozen=True, order=True)
class CurrentWitness:
    subject:Subject
    cluster_id:str
    source_id:str
    outcome:str
    observed_at:datetime
    evidence_id:str
    def __post_init__(self):
        if self.outcome not in {"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}:
            raise Refused("REFUSED[INVALID_OUTCOME]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_WITNESS_TIME]")
def admit(subject,witnesses,estimates,now,min_trials):
    est={e.source_id:e for e in estimates}
    seen=set(); admitted=[]; under=[]
    for w in witnesses:
        if w.subject!=subject: raise Refused("REFUSED[FOREIGN_SUBJECT]")
        if w.observed_at>now: raise Refused("REFUSED[FUTURE_EVIDENCE]")
        if w.evidence_id in seen: raise Refused("REFUSED[DUPLICATE_EVIDENCE_ID]")
        seen.add(w.evidence_id)
        e=est.get(w.source_id)
        if e is None or e.n < min_trials: under.append(w.source_id)
        admitted.append(w)
    return tuple(sorted(admitted)), tuple(sorted(set(under)))
