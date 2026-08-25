from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class TransportHazard:
    attempts: int
    timeout_rate: Fraction
    error_rate: Fraction
    resolved_mean_latency_ms: Fraction | None

def measure(observations):
    rows=tuple(observations)
    if not rows:
        return TransportHazard(0,Fraction(0),Fraction(0),None)
    n=len(rows)
    timeout=sum(1 for r in rows if r.status=="TIMEOUT")
    errors=sum(1 for r in rows if r.status in {"TIMEOUT","DNS_ERROR","HTTP_ERROR"})
    lat=[r.latency_ms for r in rows if r.status=="RESOLVED"]
    mean=None if not lat else Fraction(sum(lat),len(lat))
    return TransportHazard(n,Fraction(timeout,n),Fraction(errors,n),mean)
