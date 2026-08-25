from dataclasses import dataclass

@dataclass(frozen=True)
class Candidate:
    name: str
    risk: float
    shift: float
    neg_support: float
    neg_ess: float

def dominates(left, right):
    a = (left.risk, left.shift, left.neg_support, left.neg_ess)
    b = (right.risk, right.shift, right.neg_support, right.neg_ess)
    return all(x <= y for x, y in zip(a, b)) and any(x < y for x, y in zip(a, b))

def frontier(values):
    values = tuple(values)
    return tuple(sorted((item for item in values if not any(other != item and dominates(other, item) for other in values)), key=lambda item: item.name))
