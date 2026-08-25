from dataclasses import dataclass
from fractions import Fraction
import math

@dataclass(frozen=True)
class Availability:
    attempts: int
    resolved: int
    posterior_mean: Fraction
    wilson_lower: float
    wilson_upper: float

def estimate(observations, alpha=1, beta=1, z=1.959963984540054):
    rows=tuple(observations)
    n=len(rows)
    k=sum(1 for r in rows if r.status=="RESOLVED")
    posterior=Fraction(k+alpha,n+alpha+beta)
    if n==0:
        return Availability(0,0,posterior,0.0,1.0)
    p=k/n
    denom=1+z*z/n
    center=(p+z*z/(2*n))/denom
    half=(z*math.sqrt((p*(1-p)+z*z/(4*n))/n))/denom
    return Availability(n,k,posterior,max(0.0,center-half),min(1.0,center+half))
