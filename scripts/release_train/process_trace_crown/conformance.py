from __future__ import annotations
from dataclasses import dataclass
from collections import Counter
from .normalize import activity_projection
from .trace import Trace

@dataclass(frozen=True)
class Conformance:
    precision: float
    recall: float
    f1: float

def score(expected: Trace, observed: Trace) -> Conformance:
    e = Counter(activity_projection(expected))
    o = Counter(activity_projection(observed))
    matched = sum((e & o).values())
    precision = matched / max(1, sum(o.values()))
    recall = matched / max(1, sum(e.values()))
    f1 = 0.0 if precision + recall == 0 else 2 * precision * recall / (precision + recall)
    return Conformance(precision, recall, f1)
