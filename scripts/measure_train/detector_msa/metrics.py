from dataclasses import dataclass
from fractions import Fraction
from statistics import median
from .subject import Refused
from .run import admit_run

@dataclass(frozen=True)
class DetectorMetrics:
    policy_fingerprint: str
    support: int
    transitioned_cases: int
    stable_cases: int
    false_alarms: int
    misses: int
    detected: int
    false_alarm_rate: Fraction
    miss_rate: Fraction
    median_delay_seconds: Fraction

def fit_metrics(cases, runs, policy):
    matching = [run for run in runs if run.policy_fingerprint == policy.fingerprint]
    by_case = {run.case_id: run for run in matching}
    if len(by_case) != len(matching):
        raise Refused("REFUSED[DUPLICATE_DETECTOR_RUN]")
    transitioned = stable = false_alarms = misses = detected = 0
    delays = []
    for case in cases:
        run = by_case.get(case.case_id)
        if run is None:
            raise Refused("REFUSED[MISSING_DETECTOR_RUN]")
        admit_run(case, policy, run)
        if case.transition_at is None:
            stable += 1
            false_alarms += int(run.alarm_at is not None)
        else:
            transitioned += 1
            if run.alarm_at is None:
                misses += 1
            else:
                detected += 1
                micros = int((run.alarm_at - case.transition_at).total_seconds() * 1_000_000)
                delays.append(Fraction(micros, 1_000_000))
    far = Fraction(false_alarms, stable) if stable else Fraction(0)
    miss = Fraction(misses, transitioned) if transitioned else Fraction(0)
    delay = Fraction(median(delays)) if delays else Fraction(0)
    return DetectorMetrics(policy.fingerprint, len(cases), transitioned, stable, false_alarms, misses, detected, far, miss, delay)
