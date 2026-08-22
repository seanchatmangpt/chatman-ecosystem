import hashlib, json
from dataclasses import dataclass
from datetime import datetime
from .subject import Subject, Refused

@dataclass(frozen=True, order=True)
class CalibrationTrial:
    subject: Subject
    source_id: str
    truth_pass: bool
    predicted_pass: bool
    observed_at: datetime
    def __post_init__(self):
        if not self.source_id.strip(): raise Refused("REFUSED[EMPTY_SOURCE_ID]")
        if self.observed_at.tzinfo is None or self.observed_at.utcoffset() is None:
            raise Refused("REFUSED[NAIVE_TRIAL_TIME]")
    @property
    def trial_id(self):
        body={"repo":self.subject.repo,"sha":self.subject.sha,"source_id":self.source_id,
              "truth_pass":self.truth_pass,"predicted_pass":self.predicted_pass,
              "observed_at":self.observed_at.isoformat()}
        raw=json.dumps(body,sort_keys=True,separators=(",",":"))
        return hashlib.sha256(raw.encode()).hexdigest()

def admit_trials(subject, source_id, trials):
    seen=set(); out=[]
    for trial in trials:
        if trial.subject != subject: raise Refused("REFUSED[FOREIGN_TRIAL_SUBJECT]")
        if trial.source_id != source_id: raise Refused("REFUSED[FOREIGN_TRIAL_SOURCE]")
        if trial.trial_id in seen: raise Refused("REFUSED[DUPLICATE_CALIBRATION_TRIAL]")
        seen.add(trial.trial_id); out.append(trial)
    return tuple(sorted(out, key=lambda t:(t.observed_at,t.trial_id)))
