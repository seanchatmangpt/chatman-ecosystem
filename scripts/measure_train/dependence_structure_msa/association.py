import math
from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class Association:
    covariance: Fraction
    phi: float
    absolute_phi: float

def association(table):
    a,b,c,d=table.n11,table.n10,table.n01,table.n00
    den=(a+b)*(c+d)*(a+c)*(b+d)
    phi=0.0 if den == 0 else (a*d-b*c)/math.sqrt(den)
    return Association(table.covariance,phi,abs(phi))
