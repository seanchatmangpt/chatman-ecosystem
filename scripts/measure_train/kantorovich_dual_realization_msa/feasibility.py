from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class Feasibility:
    support:int; dual_feasible:bool; complementary_slackness:bool; zero_gap:bool; max_gap:Fraction
def evaluate(rows, tol=Fraction(0)):
    rs=tuple(rows)
    return Feasibility(len(rs), all(r.certificate.max_dual_violation<=tol for r in rs), all(r.certificate.max_slackness_violation<=tol for r in rs), all(abs(r.certificate.gap)<=tol for r in rs), max((abs(r.certificate.gap) for r in rs), default=Fraction(0)))
