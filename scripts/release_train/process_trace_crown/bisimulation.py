from __future__ import annotations
from dataclasses import dataclass
from .relation import Relation, exact, activity, stutter
from .partial_order import equivalent as partial_order_equivalent
from .independence import Independence
from .trace import Trace
from .refusal import Refused

@dataclass(frozen=True)
class BisimulationWitness:
    relation: Relation
    fuel: int
    accepted: bool

def witness(left: Trace, right: Trace, relation: Relation, fuel: int, independence: Independence | None = None) -> BisimulationWitness:
    if fuel <= 0 or max(len(left.events), len(right.events)) > fuel:
        raise Refused("BISIMULATION_FUEL_EXHAUSTED")
    if relation is Relation.EXACT:
        ok = exact(left, right)
    elif relation is Relation.ACTIVITY:
        ok = activity(left, right)
    elif relation is Relation.STUTTER:
        ok = stutter(left, right)
    else:
        if independence is None:
            raise Refused("INDEPENDENCE_PROOF_REQUIRED")
        ok = partial_order_equivalent(left, right, independence)
    return BisimulationWitness(relation, fuel, ok)
