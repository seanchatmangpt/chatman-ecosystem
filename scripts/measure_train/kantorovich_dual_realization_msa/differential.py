from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Differential:
    mae:Fraction; max_error:Fraction; signed_bias:Fraction
def oracle_differential(rows):
    rs=tuple(rows); n=len(rs)
    if not n: return Differential(Fraction(0),Fraction(0),Fraction(0))
    e=[r.certificate.primal-r.oracle_cost for r in rs]
    return Differential(sum(abs(x) for x in e)/n,max(abs(x) for x in e),sum(e)/n)
