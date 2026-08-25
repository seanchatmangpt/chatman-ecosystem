from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Realization:
    mae:Fraction; false_safe_rate:Fraction; support:int
def realized(rows):
    rs=tuple(rows); n=len(rs)
    if not n: return Realization(Fraction(0),Fraction(0),0)
    return Realization(sum(abs(r.certificate.primal-r.realized_cost) for r in rs)/n, Fraction(sum(1 for r in rs if r.certificate.primal<r.realized_cost),n), n)
