from __future__ import annotations
from dataclasses import dataclass
from .sample import ErrorSample

@dataclass(frozen=True)
class PageHinkleyResult:
    statistic: float
    changed: bool

def detect(samples: tuple[ErrorSample, ...], delta: float, threshold: float) -> PageHinkleyResult:
    if delta < 0 or threshold <= 0:
        raise ValueError("REFUSED[INVALID_PAGE_HINKLEY_PARAMETERS]")
    mean = 0.0
    cumulative = 0.0
    minimum = 0.0
    maximum_gap = 0.0
    for index, sample in enumerate(samples, 1):
        mean += (sample.error - mean) / index
        cumulative += sample.error - mean - delta
        minimum = min(minimum, cumulative)
        maximum_gap = max(maximum_gap, cumulative - minimum)
    return PageHinkleyResult(round(maximum_gap, 12), maximum_gap >= threshold)
