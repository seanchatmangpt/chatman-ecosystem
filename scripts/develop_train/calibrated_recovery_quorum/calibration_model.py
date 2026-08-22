from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from math import log, sqrt

from .calibration_trial import CalibrationTrial


@dataclass(frozen=True, slots=True)
class CalibrationModel:
    source_id: str
    support: int
    true_positive_rate: Fraction
    false_positive_rate: Fraction
    brier_error: Fraction
    lower_precision_bound: Fraction

    @property
    def calibrated(self) -> bool:
        return self.support > 0


def fit_calibration(
    source_id: str,
    trials: tuple[CalibrationTrial, ...],
    *,
    min_trials: int = 4,
    alpha: float = 0.05,
) -> CalibrationModel:
    own = tuple(t for t in trials if t.source_id == source_id)
    if len({t.trial_id for t in own}) != len(own):
        raise ValueError("REFUSED[DUPLICATE_CALIBRATION_TRIAL]")
    if min_trials < 1:
        raise ValueError("REFUSED[INVALID_MIN_TRIALS]")
    tp = sum(t.truth_pass and t.predicted == "PASS" for t in own)
    fn = sum(t.truth_pass and t.predicted == "FAIL" for t in own)
    fp = sum((not t.truth_pass) and t.predicted == "PASS" for t in own)
    tn = sum((not t.truth_pass) and t.predicted == "FAIL" for t in own)
    tpr = Fraction(tp + 1, tp + fn + 2)
    fpr = Fraction(fp + 1, fp + tn + 2)
    errors = sum((int(t.predicted == "PASS") - int(t.truth_pass)) ** 2 for t in own)
    brier = Fraction(errors, len(own) or 1)
    predicted_pass = tp + fp
    empirical_precision = Fraction(tp, predicted_pass) if predicted_pass else Fraction(0, 1)
    if own:
        epsilon = sqrt(log(1.0 / alpha) / (2.0 * len(own)))
        lower = max(0.0, float(empirical_precision) - epsilon)
        lower_fraction = Fraction(lower).limit_denominator(1_000_000)
    else:
        lower_fraction = Fraction(0, 1)
    if len(own) < min_trials:
        lower_fraction = Fraction(0, 1)
    return CalibrationModel(source_id, len(own), tpr, fpr, brier, lower_fraction)
