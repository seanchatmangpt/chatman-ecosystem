from dataclasses import dataclass
from fractions import Fraction
@dataclass(frozen=True)
class InformationCapital: nominal_gain:Fraction; redundancy_penalty:Fraction; effective_gain:Fraction
def score(xs,g):
    xs=tuple(xs); by={x.transport_id:x for x in xs}; nominal=sum(Fraction(str(x.information_gain)) for x in xs); penalty=Fraction(0)
    for e in g.edges:
        if e.left in by and e.right in by: penalty += max(Fraction(0),e.rho)*min(Fraction(str(by[e.left].information_gain)),Fraction(str(by[e.right].information_gain)))
    return InformationCapital(nominal,penalty,max(Fraction(0),nominal-penalty))
