from dataclasses import dataclass
from fractions import Fraction
from .subject import Refused

@dataclass(frozen=True)
class CusumResult:
    state: str
    positive: Fraction
    negative: Fraction
    first_crossing: int | None

def detect_error_shift(trials, baseline_error, threshold=Fraction(3,2), slack=Fraction(1,20), min_trials=4):
    if not (Fraction(0) <= baseline_error <= Fraction(1)): raise Refused("REFUSED[INVALID_BASELINE_ERROR]")
    if threshold <= 0 or slack < 0: raise Refused("REFUSED[INVALID_CUSUM_PARAMETER]")
    if len(trials) < min_trials: return CusumResult("INSUFFICIENT",Fraction(0),Fraction(0),None)
    pos=neg=Fraction(0); crossing=None
    for index, trial in enumerate(trials,1):
        error=Fraction(int(trial.truth_pass != trial.predicted_pass),1)
        pos=max(Fraction(0),pos + error - baseline_error - slack)
        neg=max(Fraction(0),neg + baseline_error - error - slack)
        if crossing is None and max(pos,neg) >= threshold: crossing=index
    return CusumResult("DRIFT" if crossing is not None else "STABLE",pos,neg,crossing)
