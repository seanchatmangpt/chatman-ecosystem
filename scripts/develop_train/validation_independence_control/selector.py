from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
class Strategy(str,Enum):
    MAX_COVERAGE="MAX_COVERAGE"
    MIN_WIDTH="MIN_WIDTH"
    MIN_OVERLAP="MIN_OVERLAP"
    MINIMAX_MISS="MINIMAX_MISS"
@dataclass(frozen=True)
class Candidate:
    name: str
    coverage: Fraction
    width: Fraction
    overlap: Fraction
    miss: Fraction
    cost: Fraction
def select(candidates,strategy):
    xs=list(candidates)
    if strategy==Strategy.MAX_COVERAGE: key=lambda c:(-c.coverage,c.width,c.name)
    elif strategy==Strategy.MIN_WIDTH: key=lambda c:(c.width,-c.coverage,c.name)
    elif strategy==Strategy.MIN_OVERLAP: key=lambda c:(c.overlap,c.width,c.name)
    else: key=lambda c:(c.miss,c.width,c.name)
    return sorted(xs,key=key)[0]
def pareto(candidates):
    xs=list(candidates); out=[]
    for c in xs:
        dominated=any(
            o is not c and o.coverage>=c.coverage and o.width<=c.width and o.overlap<=c.overlap and o.cost<=c.cost
            and (o.coverage>c.coverage or o.width<c.width or o.overlap<c.overlap or o.cost<c.cost)
            for o in xs)
        if not dominated: out.append(c)
    return tuple(sorted(out,key=lambda x:x.name))
