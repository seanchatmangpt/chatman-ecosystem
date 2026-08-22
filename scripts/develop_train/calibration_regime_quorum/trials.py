from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib, json
from .subject import Refusal

def _aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None

@dataclass(frozen=True, slots=True)
class CalibrationTrial:
    source_id: str
    truth_pass: bool
    predicted_pass: bool
    observed_at: datetime
    def __post_init__(self) -> None:
        if not self.source_id.strip(): raise Refusal("REFUSED[EMPTY_CALIBRATION_SOURCE]")
        if not _aware(self.observed_at): raise Refusal("REFUSED[NAIVE_CALIBRATION_TIME]")
    @property
    def trial_id(self) -> str:
        body={"observed_at":self.observed_at.astimezone(timezone.utc).isoformat(),"predicted_pass":self.predicted_pass,"source_id":self.source_id,"truth_pass":self.truth_pass}
        return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def admit_trials(trials: list[CalibrationTrial], *, now: datetime) -> tuple[CalibrationTrial, ...]:
    if not _aware(now): raise Refusal("REFUSED[NAIVE_NOW]")
    seen:set[str]=set(); ordered=sorted(trials,key=lambda t:(t.observed_at,t.trial_id))
    for trial in ordered:
        if trial.observed_at > now: raise Refusal("REFUSED[FUTURE_CALIBRATION_TRIAL]")
        if trial.trial_id in seen: raise Refusal("REFUSED[DUPLICATE_CALIBRATION_TRIAL]")
        seen.add(trial.trial_id)
    return tuple(ordered)
