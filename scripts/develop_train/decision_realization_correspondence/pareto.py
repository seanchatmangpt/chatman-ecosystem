from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Candidate:
    name: str
    loss: Fraction
    defer_rate: Fraction
    calibration_gap: Fraction
    cost: Fraction

def dominates(a,b):
    weak=(a.loss<=b.loss and a.defer_rate<=b.defer_rate and a.calibration_gap<=b.calibration_gap and a.cost<=b.cost)
    strict=(a.loss<b.loss or a.defer_rate<b.defer_rate or a.calibration_gap<b.calibration_gap or a.cost<b.cost)
    return weak and strict

def frontier(candidates):
    return tuple(c for c in candidates if not any(dominates(o,c) for o in candidates if o is not c))
