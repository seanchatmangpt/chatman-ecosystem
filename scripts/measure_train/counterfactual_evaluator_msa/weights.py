from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused

@dataclass(frozen=True)
class WeightDiagnostics:
    n: int
    ess: Fraction
    max_weight: Fraction
    mean_weight: Fraction
    max_to_mean: Fraction

def importance_weight(case):
    if case.behavior_propensity <= 0: raise Refused("REFUSED[POSITIVITY_VIOLATION]")
    return case.target_propensity / case.behavior_propensity

def weight_diagnostics(cases):
    ws=[importance_weight(c) for c in cases]
    if not ws: return WeightDiagnostics(0,Fraction(0),Fraction(0),Fraction(0),Fraction(0))
    total=sum(ws,Fraction(0)); squares=sum((w*w for w in ws),Fraction(0))
    ess=Fraction(0) if squares==0 else total*total/squares
    mean=total/len(ws); maximum=max(ws)
    ratio=Fraction(0) if mean==0 else maximum/mean
    return WeightDiagnostics(len(ws),ess,maximum,mean,ratio)
