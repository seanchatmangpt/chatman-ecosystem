from dataclasses import dataclass
from datetime import datetime
from fractions import Fraction
from .subject import Refused
@dataclass(frozen=True, order=True)
class Interval:
    start:datetime; end:datetime
    def __post_init__(self):
        if self.start.tzinfo is None or self.end.tzinfo is None: raise Refused("REFUSED[NAIVE_INTERVAL]")
        if self.end <= self.start: raise Refused("REFUSED[EMPTY_INTERVAL]")
    def micros(self):
        return int((self.end-self.start).total_seconds()*1_000_000)
def intersection(intervals):
    xs=tuple(intervals)
    if not xs: raise Refused("REFUSED[EMPTY_INTERVAL_SET]")
    s=max(x.start for x in xs); e=min(x.end for x in xs)
    return None if e<=s else Interval(s,e)
def overlap_ratio(intervals):
    xs=tuple(intervals); common=intersection(xs)
    if common is None: return Fraction(0,1)
    union_start=min(x.start for x in xs); union_end=max(x.end for x in xs)
    return Fraction(common.micros(), int((union_end-union_start).total_seconds()*1_000_000))
