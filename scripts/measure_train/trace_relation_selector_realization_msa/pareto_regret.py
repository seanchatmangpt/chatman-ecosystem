from dataclasses import dataclass
from .relation import stronger_than

@dataclass(frozen=True, order=True)
class OutcomeVector:
    relation: object
    error_ppm: int
    cost_micros: int

def dominates(a,b):
    relation_ok=a.relation==b.relation or stronger_than(a.relation,b.relation)
    numeric_ok=a.error_ppm<=b.error_ppm and a.cost_micros<=b.cost_micros
    strict=(a.relation!=b.relation) or a.error_ppm<b.error_ppm or a.cost_micros<b.cost_micros
    return relation_ok and numeric_ok and strict

def frontier(vectors):
    rows=tuple(vectors)
    return tuple(sorted(v for v in rows if not any(dominates(other,v) for other in rows if other!=v)))

def chosen_is_pareto(decision, vectors):
    survivors={v.relation for v in frontier(vectors)}
    return any(r in survivors for r in decision.chosen)
