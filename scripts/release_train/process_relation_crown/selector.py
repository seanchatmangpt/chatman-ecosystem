from dataclasses import dataclass
from enum import Enum
from .relation import Relation
class Strategy(str,Enum):
    STRONGEST_DEFENSIBLE="STRONGEST_DEFENSIBLE"; MINIMAX_ERROR="MINIMAX_ERROR"; PARETO_ERROR_COST="PARETO_ERROR_COST"; INFORMATION_GAIN="INFORMATION_GAIN"
@dataclass(frozen=True)
class Candidate:
    relation:Relation; fe:float; fr:float; cost:float; information:float
def pareto(rows):
    out=[]
    for a in rows:
        dominated=any((b.fe<=a.fe and b.fr<=a.fr and b.cost<=a.cost and (b.fe<a.fe or b.fr<a.fr or b.cost<a.cost)) for b in rows if b!=a)
        if not dominated: out.append(a)
    return tuple(out)
def select(rows,strategy:Strategy):
    rows=tuple(rows)
    if not rows: return None
    if strategy==Strategy.STRONGEST_DEFENSIBLE:
        rank={Relation.EXACT:0,Relation.STUTTER:1,Relation.PARTIAL_ORDER:1,Relation.ACTIVITY:2}
        return min(rows,key=lambda c:(rank[c.relation],c.fe+c.fr,c.cost,c.relation.value))
    if strategy==Strategy.MINIMAX_ERROR: return min(rows,key=lambda c:(max(c.fe,c.fr),c.cost,c.relation.value))
    if strategy==Strategy.PARETO_ERROR_COST: return min(pareto(rows),key=lambda c:(c.fe+c.fr+c.cost,c.relation.value))
    return max(rows,key=lambda c:(c.information,-c.cost,c.relation.value))
