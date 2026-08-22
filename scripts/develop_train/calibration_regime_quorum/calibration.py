from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction
from .subject import Refusal
from .trials import CalibrationTrial

@dataclass(frozen=True, slots=True)
class CalibrationModel:
    source_id:str; support:int; tp:int; tn:int; fp:int; fn:int; tpr:Fraction; fpr:Fraction; brier:Fraction

def fit_model(trials:tuple[CalibrationTrial,...],*,source_id:str,min_trials:int=4)->CalibrationModel:
    rows=[t for t in trials if t.source_id==source_id]
    if len(rows)<min_trials: raise Refusal("REFUSED[INSUFFICIENT_CALIBRATION_SUPPORT]")
    tp=sum(t.truth_pass and t.predicted_pass for t in rows); tn=sum((not t.truth_pass) and (not t.predicted_pass) for t in rows)
    fp=sum((not t.truth_pass) and t.predicted_pass for t in rows); fn=sum(t.truth_pass and (not t.predicted_pass) for t in rows)
    tpr=Fraction(tp+1,tp+fn+2); fpr=Fraction(fp+1,fp+tn+2); errors=sum(t.truth_pass!=t.predicted_pass for t in rows)
    return CalibrationModel(source_id,len(rows),tp,tn,fp,fn,tpr,fpr,Fraction(errors,len(rows)))
