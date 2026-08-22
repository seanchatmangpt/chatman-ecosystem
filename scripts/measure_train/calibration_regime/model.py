import hashlib, json
from dataclasses import dataclass
from fractions import Fraction
from .subject import Subject, Refused
from .window import CalibrationWindow

@dataclass(frozen=True)
class CalibrationModel:
    subject: Subject
    source_id: str
    window: CalibrationWindow
    support: int
    tp: int
    tn: int
    fp: int
    fn: int
    tpr: Fraction
    fpr: Fraction
    brier: Fraction
    @property
    def model_id(self):
        body={"repo":self.subject.repo,"sha":self.subject.sha,"source":self.source_id,
              "start":self.window.start.isoformat(),"end":self.window.end.isoformat(),"support":self.support,
              "tp":self.tp,"tn":self.tn,"fp":self.fp,"fn":self.fn}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def fit_model(subject, source_id, window, trials):
    selected=window.select(trials)
    if len(selected) < window.min_trials: raise Refused("REFUSED[INSUFFICIENT_CALIBRATION_WINDOW]")
    tp=sum(t.truth_pass and t.predicted_pass for t in selected)
    tn=sum((not t.truth_pass) and (not t.predicted_pass) for t in selected)
    fp=sum((not t.truth_pass) and t.predicted_pass for t in selected)
    fn=sum(t.truth_pass and (not t.predicted_pass) for t in selected)
    tpr=Fraction(tp+1,tp+fn+2)
    fpr=Fraction(fp+1,fp+tn+2)
    brier=Fraction(fp+fn,len(selected))
    return CalibrationModel(subject,source_id,window,len(selected),tp,tn,fp,fn,tpr,fpr,brier)
