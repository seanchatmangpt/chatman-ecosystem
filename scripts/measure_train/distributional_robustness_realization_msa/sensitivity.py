from dataclasses import dataclass
from fractions import Fraction
from .refusal import Refused
@dataclass(frozen=True)
class RadiusSensitivity:
    max_slope:Fraction; mean_slope:Fraction
def finite_difference(points):
    rows=sorted((Fraction(r),Fraction(loss)) for r,loss in points); slopes=[]
    for (r0,l0),(r1,l1) in zip(rows,rows[1:]):
        if r1==r0: raise Refused("REFUSED[DUPLICATE_RADIUS]")
        slopes.append((l1-l0)/(r1-r0))
    if not slopes: return RadiusSensitivity(Fraction(0),Fraction(0))
    return RadiusSensitivity(max(abs(s) for s in slopes),sum(slopes,Fraction(0))/len(slopes))
