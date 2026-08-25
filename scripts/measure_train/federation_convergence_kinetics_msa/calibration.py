from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Calibration:
    support: int
    brier: Fraction
    false_on_time: Fraction
    missed_on_time: Fraction
    state: str

def calibrate(observations, deadline_truth, min_support=10, max_brier=Fraction(1, 5), max_directional=Fraction(1, 5)):
    rows = tuple(observations)
    n = len(rows)
    if not n:
        return Calibration(0, Fraction(0), Fraction(0), Fraction(0), "INSUFFICIENT")
    brier = sum(((row.predicted_on_time - Fraction(int(deadline_truth[row.episode_id]))) ** 2 for row in rows), Fraction(0)) / n
    false_on_time = sum(1 for row in rows if row.predicted_on_time >= Fraction(1, 2) and not deadline_truth[row.episode_id])
    missed_on_time = sum(1 for row in rows if row.predicted_on_time < Fraction(1, 2) and deadline_truth[row.episode_id])
    false_rate = Fraction(false_on_time, n)
    missed_rate = Fraction(missed_on_time, n)
    state = "INSUFFICIENT" if n < min_support else ("CALIBRATED" if brier <= max_brier and false_rate <= max_directional and missed_rate <= max_directional else "UNRELIABLE")
    return Calibration(n, brier, false_rate, missed_rate, state)
