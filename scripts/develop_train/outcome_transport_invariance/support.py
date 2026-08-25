from dataclasses import dataclass
from .errors import Refused

@dataclass(frozen=True)
class Support:
    overlap: float
    unsupported: float
    min_source: float

def analyze(source, target):
    s, t = source.data(), target.data()
    cells = set(s) | set(t)
    positive = [s.get(k, 0) for k in t if t[k] > 0 and s.get(k, 0) > 0]
    return Support(
        sum(min(s.get(k, 0), t.get(k, 0)) for k in cells),
        sum(t.get(k, 0) for k in cells if t.get(k, 0) > 0 and s.get(k, 0) <= 0),
        min(positive) if positive else 0,
    )

def require(source, target, minimum=1e-9):
    result = analyze(source, target)
    if result.unsupported > 1e-12 or result.min_source < minimum:
        raise Refused("POSITIVITY_VIOLATION")
    return result
