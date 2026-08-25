from dataclasses import dataclass
from math import sqrt, log
from .subject import Refused
@dataclass(frozen=True)
class CalibrationEstimate:
    source_id:str
    n:int
    true_positive_rate:float
    false_positive_rate:float
    brier_score:float
    lower_precision_bound:float

def estimate(source_id, trials, delta=0.05):
    rows=[t for t in trials if t.source_id==source_id]
    ids=[t.trial_id for t in rows]
    if len(ids)!=len(set(ids)): raise Refused("REFUSED[DUPLICATE_CALIBRATION_TRIAL]")
    if not (0 < delta < 1): raise Refused("REFUSED[INVALID_DELTA]")
    n=len(rows)
    if n==0: return CalibrationEstimate(source_id,0,0.0,1.0,1.0,0.0)
    tp=sum(t.predicted_positive and t.truth_positive for t in rows)
    fp=sum(t.predicted_positive and not t.truth_positive for t in rows)
    pos=sum(t.truth_positive for t in rows)
    neg=n-pos
    tpr=(tp+1)/(pos+2)
    fpr=(fp+1)/(neg+2)
    brier=sum((int(t.predicted_positive)-int(t.truth_positive))**2 for t in rows)/n
    predicted=sum(t.predicted_positive for t in rows)
    precision=(tp+1)/(predicted+2)
    radius=sqrt(log(1/delta)/(2*n))
    return CalibrationEstimate(source_id,n,tpr,fpr,brier,max(0.0,precision-radius))
