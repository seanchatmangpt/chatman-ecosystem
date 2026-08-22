from dataclasses import dataclass
from fractions import Fraction
from .interval import intersection, overlap_ratio
@dataclass(frozen=True)
class Synchrony:
    common_micros:int
    overlap:Fraction
    max_end_skew_micros:int
def measure_synchrony(epochs):
    xs=tuple(epochs)
    common=intersection([e.window for e in xs])
    ends=[e.window.end for e in xs]
    skew=int((max(ends)-min(ends)).total_seconds()*1_000_000)
    return Synchrony(0 if common is None else common.micros(), overlap_ratio([e.window for e in xs]), skew)
