from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Calibration:
    support: int
    false_current_rate: Fraction
    false_stale_rate: Fraction
    state: str

def calibrate(rows, min_support=5, max_false_current=Fraction(1, 10)):
    rows = tuple(rows)
    if not rows:
        return Calibration(0, Fraction(0), Fraction(0), "INSUFFICIENT")
    n = len(rows)
    false_current = Fraction(sum(row.false_current for row in rows), n)
    false_stale = Fraction(sum(row.false_stale for row in rows), n)
    state = "INSUFFICIENT" if n < min_support else ("CALIBRATED" if false_current <= max_false_current else "UNRELIABLE")
    return Calibration(n, false_current, false_stale, state)
