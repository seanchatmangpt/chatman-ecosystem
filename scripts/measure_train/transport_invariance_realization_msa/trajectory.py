from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True,order=True)
class StressPoint:
    magnitude:Fraction
    observed_risk:Fraction
    observed_success:bool
@dataclass(frozen=True)
class Monotonicity:
    violations:int
    pairs:int
    violation_rate:Fraction
@dataclass(frozen=True)
class Sensitivity:
    max_slope:Fraction
    mean_slope:Fraction
    finite_differences:tuple
@dataclass(frozen=True)
class ThresholdEstimate:
    first_failure:Fraction|None
    last_success:Fraction|None
    width:Fraction|None
def trajectory(cases):
    rows=sorted(StressPoint(c.stress.magnitude,c.observed_risk,c.observed_success) for c in cases)
    if len({p.magnitude for p in rows})!=len(rows): raise Refused("REFUSED[DUPLICATE_STRESS_MAGNITUDE]")
    return tuple(rows)
def risk_monotonicity(points,tolerance=Fraction(0)):
    rows=tuple(points); v=sum(1 for a,b in zip(rows,rows[1:]) if b.observed_risk+tolerance<a.observed_risk); p=max(0,len(rows)-1)
    return Monotonicity(v,p,Fraction(v,p) if p else Fraction(0))
def local_sensitivity(points):
    rows=tuple(points); diffs=[]
    for a,b in zip(rows,rows[1:]):
        dm=b.magnitude-a.magnitude
        if dm: diffs.append(abs(b.observed_risk-a.observed_risk)/dm)
    return Sensitivity(max(diffs) if diffs else Fraction(0),sum(diffs,Fraction(0))/len(diffs) if diffs else Fraction(0),tuple(diffs))
def estimate_threshold(points):
    rows=tuple(points); success=[p.magnitude for p in rows if p.observed_success]; failure=[p.magnitude for p in rows if not p.observed_success]
    last=max(success) if success else None; first=min(failure) if failure else None
    if last is not None and first is not None and first<last: raise Refused("REFUSED[NON_MONOTONE_FAILURE_THRESHOLD]")
    return ThresholdEstimate(first,last,(first-last) if first is not None and last is not None else None)
