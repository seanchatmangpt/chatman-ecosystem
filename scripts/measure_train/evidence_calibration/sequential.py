from dataclasses import dataclass
from .likelihood import contribution
@dataclass(frozen=True)
class SequentialResult:
    log_lr:float
    decision:str
    contributions:tuple
def sequential_test(witnesses, estimates, accept_log_lr, reject_log_lr):
    est={e.source_id:e for e in estimates}
    rows=[]
    for w in witnesses:
        e=est.get(w.source_id)
        if e is None: continue
        rows.append(contribution(e,w.outcome))
    total=sum(r.log_lr for r in rows)
    if any(w.outcome=="FAIL" for w in witnesses): decision="REJECT"
    elif total >= accept_log_lr: decision="ACCEPT_BOUNDED"
    elif total <= reject_log_lr: decision="REJECT"
    else: decision="CONTINUE"
    return SequentialResult(total,decision,tuple(sorted(rows,key=lambda r:(r.source_id,r.outcome))))
