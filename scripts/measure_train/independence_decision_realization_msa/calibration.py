from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class RiskCalibration:
    support:int; brier:Fraction; predicted_independence:Fraction; observed_independence:Fraction; absolute_gap:Fraction; state:str
def calibrate(rows,min_support=8,max_gap=Fraction(1,5)):
    rows=tuple(rows); n=len(rows)
    if n==0: return RiskCalibration(0,Fraction(0),Fraction(0),Fraction(0),Fraction(0),"INSUFFICIENT")
    probs=[r.predicted_independence for r in rows]; truths=[Fraction(1) if r.truth=="INDEPENDENT" else Fraction(0) for r in rows]
    brier=sum(((p-y)*(p-y) for p,y in zip(probs,truths)),Fraction(0))/n
    pred=sum(probs,Fraction(0))/n; obs=sum(truths,Fraction(0))/n; gap=abs(pred-obs)
    state="INSUFFICIENT" if n<min_support else ("CALIBRATED" if gap<=max_gap else "UNRELIABLE")
    return RiskCalibration(n,brier,pred,obs,gap,state)
