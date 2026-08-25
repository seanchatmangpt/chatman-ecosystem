from dataclasses import dataclass
from .errors import Refused
from .relation import Relation,equivalent as seqeq
from .partial_order import equivalent as poeq
@dataclass(frozen=True)
class BisimulationWitness:
    relation:Relation; matched:bool; explored:int; fuel:int
def witness(a,b,relation,fuel=1000,independence=None):
    if fuel<=0: raise Refused("FUEL_EXHAUSTED")
    r=Relation(relation); cost=len(a.events)+len(b.events)
    if cost>fuel: raise Refused("FUEL_EXHAUSTED")
    ok=poeq(a,b,independence) if r is Relation.PARTIAL_ORDER else seqeq(a,b,r)
    return BisimulationWitness(r,ok,cost,fuel)
