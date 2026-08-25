from dataclasses import dataclass
from math import log
from .subject import Refused
@dataclass(frozen=True)
class LikelihoodContribution:
    source_id:str
    outcome:str
    log_lr:float
def contribution(estimate, outcome):
    if outcome not in {"PASS","FAIL","PENDING","UNKNOWN","UNSUPPORTED"}:
        raise Refused("REFUSED[INVALID_OUTCOME]")
    if outcome in {"PENDING","UNKNOWN","UNSUPPORTED"}:
        return LikelihoodContribution(estimate.source_id,outcome,0.0)
    eps=1e-12
    tpr=min(max(estimate.true_positive_rate,eps),1-eps)
    fpr=min(max(estimate.false_positive_rate,eps),1-eps)
    value=log(tpr/fpr) if outcome=="PASS" else log((1-tpr)/(1-fpr))
    return LikelihoodContribution(estimate.source_id,outcome,value)
