from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused

@dataclass(frozen=True)
class Prediction:
    activity: str
    support: int
    probability: Fraction


def next_activity(traces: tuple[tuple[str, ...], ...], prefix: tuple[str, ...], min_support: int = 2) -> tuple[Prediction, ...]:
    if min_support <= 0:
        raise Refused("PREDICTION_SUPPORT")
    counts: Counter[str] = Counter()
    total = 0
    for trace in traces:
        if len(trace) > len(prefix) and trace[:len(prefix)] == prefix:
            counts[trace[len(prefix)]] += 1; total += 1
    if total < min_support:
        raise Refused("PREDICTION_UNDER_SUPPORTED", str(total))
    return tuple(Prediction(a, n, Fraction(n, total)) for a, n in sorted(counts.items()))
