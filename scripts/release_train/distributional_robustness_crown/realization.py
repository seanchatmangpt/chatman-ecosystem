from dataclasses import dataclass
from .refusal import Refused
@dataclass(frozen=True)
class Realization:
    predicted_stable:bool; observed_success:bool; predicted_risk:float; stress:float
    def __post_init__(self):
        if not 0<=self.predicted_risk<=1 or self.stress<0: raise Refused("INVALID_REALIZATION")
def realization_metrics(cases,false_stable_cost=4.0,false_unstable_cost=1.0):
    if not cases: raise Refused("EMPTY_REALIZATION_CORPUS")
    fs=sum(c.predicted_stable and not c.observed_success for c in cases)
    fu=sum((not c.predicted_stable) and c.observed_success for c in cases)
    realized=[0.0 if c.observed_success else 1.0 for c in cases]
    mae=sum(abs(c.predicted_risk-y) for c,y in zip(cases,realized))/len(cases)
    bias=sum(c.predicted_risk-y for c,y in zip(cases,realized))/len(cases)
    loss=(fs*false_stable_cost+fu*false_unstable_cost)/len(cases)
    return {"false_stable":fs,"false_unstable":fu,"mae":mae,"bias":bias,"loss":loss}
def monotone_stress(cases):
    ordered=sorted(cases,key=lambda c:c.stress)
    return all(a.predicted_risk<=b.predicted_risk for a,b in zip(ordered,ordered[1:]))
