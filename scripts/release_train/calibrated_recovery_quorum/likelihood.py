import math
from dataclasses import dataclass
@dataclass(frozen=True)
class LikelihoodContribution:
    value: float; informative: bool

def contribution(model,outcome):
    if outcome in {"PENDING","UNKNOWN","UNSUPPORTED"}: return LikelihoodContribution(0.0,False)
    if outcome=="PASS": return LikelihoodContribution(math.log(model.tpr/model.fpr),True)
    if outcome=="FAIL": return LikelihoodContribution(math.log((1-model.tpr)/(1-model.fpr)),True)
    raise ValueError(outcome)
