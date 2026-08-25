from dataclasses import dataclass
from fractions import Fraction
from .errors import Refused
from .provenance import require_distinct
@dataclass(frozen=True)
class Dependence:
    overlap: Fraction
    phi: Fraction
    mutual_information: Fraction
    generation: int
    digest: str
    def __post_init__(self):
        if not (0 <= self.overlap <= 1) or self.mutual_information < 0 or self.generation < 0 or len(self.digest)!=64:
            raise Refused("INVALID_DEPENDENCE")
def ancestry_overlap(graph, a: str, b: str):
    aa=set(graph.ancestors(a))|{a}; bb=set(graph.ancestors(b))|{b}
    union=aa|bb
    return Fraction(len(aa&bb), len(union)) if union else Fraction(0)
def effective_independence(graph, a, b, pa, pb, dependence: Dependence):
    require_distinct(pa,pb)
    overlap=ancestry_overlap(graph,a,b)
    if overlap != 0 or dependence.overlap != 0 or dependence.phi != 0 or dependence.mutual_information != 0:
        raise Refused("EMPIRICAL_DEPENDENCE")
    return True
