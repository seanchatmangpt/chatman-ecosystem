from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class KaplanMeierPoint:
    latency_ms: int
    at_risk: int
    resolved: int
    censored: int
    survival: Fraction

def resolution_survival(observations):
    rows=sorted(observations,key=lambda r:(r.latency_ms,r.evidence_id))
    if not rows:
        return ()
    times=sorted({r.latency_ms for r in rows})
    survival=Fraction(1)
    points=[]
    for t in times:
        at_risk=sum(1 for r in rows if r.latency_ms >= t)
        resolved=sum(1 for r in rows if r.latency_ms==t and r.status=="RESOLVED")
        censored=sum(1 for r in rows if r.latency_ms==t and r.status!="RESOLVED")
        if at_risk and resolved:
            survival *= Fraction(at_risk-resolved,at_risk)
        points.append(KaplanMeierPoint(t,at_risk,resolved,censored,survival))
    return tuple(points)

def median_resolution_latency(observations):
    for p in resolution_survival(observations):
        if p.survival <= Fraction(1,2):
            return p.latency_ms
    return None
