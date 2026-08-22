from __future__ import annotations
from dataclasses import dataclass
from .sample import ErrorSample

@dataclass(frozen=True)
class CusumResult:
    score: float
    changed: bool

def detect(samples: tuple[ErrorSample, ...], target: float, slack: float, threshold: float) -> CusumResult:
    if not 0 <= target <= 1 or slack < 0 or threshold <= 0:
        raise ValueError("REFUSED[INVALID_CUSUM_PARAMETERS]")
    score = 0.0
    peak = 0.0
    for sample in samples:
        score = max(0.0, score + sample.error - target - slack)
        peak = max(peak, score)
    return CusumResult(round(peak, 12), peak >= threshold)
