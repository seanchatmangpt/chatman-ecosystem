from __future__ import annotations
from dataclasses import dataclass
from .sample import ErrorSample

@dataclass(frozen=True)
class EwmaResult:
    level: float
    changed: bool

def detect(samples: tuple[ErrorSample, ...], baseline: float, alpha: float, threshold: float) -> EwmaResult:
    if not 0 <= baseline <= 1 or not 0 < alpha <= 1 or threshold <= 0:
        raise ValueError("REFUSED[INVALID_EWMA_PARAMETERS]")
    level = baseline
    changed = False
    for sample in samples:
        level = alpha * sample.error + (1 - alpha) * level
        changed = changed or abs(level - baseline) >= threshold
    return EwmaResult(round(level, 12), changed)
