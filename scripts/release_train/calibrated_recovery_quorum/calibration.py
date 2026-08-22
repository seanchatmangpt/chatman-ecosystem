from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from .subject import Refused

def _utc(dt):
    if dt.tzinfo is None or dt.utcoffset() is None: raise Refused("REFUSED[NAIVE_CALIBRATION_TIME]")
    return dt.astimezone(timezone.utc)

@dataclass(frozen=True)
class CalibrationTrial:
    source_id: str; truth_pass: bool; predicted_pass: bool; observed_at: datetime
    @property
    def trial_id(self):
        body=[self.source_id,self.truth_pass,self.predicted_pass,_utc(self.observed_at).isoformat()]
        return sha256(json.dumps(body,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class CalibrationModel:
    source_id: str; support: int; true_pos: int; false_pos: int; true_neg: int; false_neg: int
    @classmethod
    def fit(cls, source_id, trials):
        rows=list(trials)
        if len({t.trial_id for t in rows}) != len(rows): raise Refused("REFUSED[DUPLICATE_CALIBRATION_TRIAL]")
        if any(t.source_id != source_id for t in rows): raise Refused("REFUSED[CALIBRATION_SOURCE_MISMATCH]")
        tp=sum(t.truth_pass and t.predicted_pass for t in rows); fp=sum((not t.truth_pass) and t.predicted_pass for t in rows)
        tn=sum((not t.truth_pass) and (not t.predicted_pass) for t in rows); fn=sum(t.truth_pass and (not t.predicted_pass) for t in rows)
        return cls(source_id,len(rows),tp,fp,tn,fn)
    @property
    def tpr(self): return (self.true_pos+1)/(self.true_pos+self.false_neg+2)
    @property
    def fpr(self): return (self.false_pos+1)/(self.false_pos+self.true_neg+2)
