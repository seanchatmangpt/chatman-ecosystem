from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Calibration:
    support: int
    mean_predicted: Fraction
    mean_observed: Fraction
    gap: Fraction
    admitted: bool

def brier(observations):
    labeled=[o for o in observations if o.truth is not None and o.decision!="DEFER"]
    if not labeled:
        return None
    vals=[]
    for o in labeled:
        y=Fraction(1) if o.truth=="INDEPENDENT" else Fraction()
        p=1-o.predicted_risk
        vals.append((p-y)*(p-y))
    return sum(vals, Fraction())/len(vals)

def calibrate(observations, minimum_support=3, max_gap=Fraction(1,5)):
    labeled=[o for o in observations if o.truth is not None]
    if not labeled:
        return Calibration(0,Fraction(),Fraction(),Fraction(1),False)
    mp=sum((o.predicted_risk for o in labeled), Fraction())/len(labeled)
    observed=sum((Fraction(o.decision!=o.truth) for o in labeled), Fraction())/len(labeled)
    gap=abs(mp-observed)
    return Calibration(len(labeled),mp,observed,gap,len(labeled)>=minimum_support and gap<=max_gap)
