from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
import hashlib

from .subject import Refusal, Subject
from .window import CalibrationWindow, utc

@dataclass(frozen=True)
class CalibrationTrial:
    subject: Subject
    source_id: str
    truth_pass: bool
    predicted_pass: bool
    observed_at: datetime

    def __post_init__(self) -> None:
        if not self.source_id:
            raise Refusal('REFUSED[EMPTY_SOURCE]')
        object.__setattr__(self, 'observed_at', utc(self.observed_at))

    @property
    def trial_id(self) -> str:
        payload = f'{self.subject.exact}|{self.source_id}|{int(self.truth_pass)}|{int(self.predicted_pass)}|{self.observed_at.isoformat()}'
        return hashlib.sha256(payload.encode()).hexdigest()

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


def fit_model(subject: Subject, source_id: str, window: CalibrationWindow, trials: list[CalibrationTrial], min_trials: int = 4) -> CalibrationModel:
    selected = [t for t in trials if t.subject == subject and t.source_id == source_id and window.contains(t.observed_at)]
    ids = [t.trial_id for t in selected]
    if len(ids) != len(set(ids)):
        raise Refusal('REFUSED[DUPLICATE_CALIBRATION_TRIAL]')
    if len(selected) < min_trials:
        raise Refusal('REFUSED[CALIBRATION_UNDER_SUPPORTED]')
    tp = sum(t.truth_pass and t.predicted_pass for t in selected)
    tn = sum((not t.truth_pass) and (not t.predicted_pass) for t in selected)
    fp = sum((not t.truth_pass) and t.predicted_pass for t in selected)
    fn = sum(t.truth_pass and (not t.predicted_pass) for t in selected)
    n = len(selected)
    tpr = Fraction(tp + 1, tp + fn + 2)
    fpr = Fraction(fp + 1, fp + tn + 2)
    brier = Fraction(fp + fn, n)
    return CalibrationModel(subject, source_id, window, n, tp, tn, fp, fn, tpr, fpr, brier)
