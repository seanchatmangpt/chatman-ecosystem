from dataclasses import dataclass

@dataclass(frozen=True)
class Candidate:
    name: str
    risk_upper: float
    calibration_gap: float
    cost: float
    uncertainty: float

def dominates(a: Candidate, b: Candidate):
    av = (a.risk_upper, a.calibration_gap, a.cost, a.uncertainty)
    bv = (b.risk_upper, b.calibration_gap, b.cost, b.uncertainty)
    return all(x <= y for x,y in zip(av,bv)) and any(x < y for x,y in zip(av,bv))

def frontier(candidates):
    cs = tuple(candidates)
    return tuple(sorted((c for c in cs if not any(dominates(o,c) for o in cs if o != c)), key=lambda c:c.name))
