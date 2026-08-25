from dataclasses import dataclass
from fractions import Fraction

@dataclass(frozen=True)
class RealizedError:
    support: int
    false_equivalence_rate: Fraction
    false_refusal_rate: Fraction

def realized_error(rows, expected_equivalent):
    rows=tuple(rows)
    if not rows:
        return RealizedError(0,Fraction(0),Fraction(0))
    fe=sum(1 for r in rows if r.equivalent and not expected_equivalent.get(r.relation,False))
    fr=sum(1 for r in rows if (not r.equivalent) and expected_equivalent.get(r.relation,False))
    n=len(rows)
    return RealizedError(n,Fraction(fe,n),Fraction(fr,n))
