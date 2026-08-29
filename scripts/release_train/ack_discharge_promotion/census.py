from __future__ import annotations
from dataclasses import dataclass
from .subject import Subject
from .witness import Witness
from .graph import DependencyGraph
from .invalidation import Invalidation

@dataclass(frozen=True)
class CensusRow:
    consumer: Subject
    depth: int
    state: str
    result: str | None

def census(invalidation: Invalidation, graph: DependencyGraph, admitted: dict[Subject,tuple[Witness,...]]) -> tuple[CensusRow,...]:
    rows=[]
    for consumer, depth in graph.affected(invalidation.producer):
        history=admitted.get(consumer,())
        if not history:
            state,result="PENDING_DELIVERY",None
        else:
            last=history[-1]
            if last.state=="DELIVERED":
                state,result="PENDING_ACK",None
            elif last.state=="ACKNOWLEDGED":
                state,result="PENDING_DISCHARGE",None
            else:
                state,result=last.result,last.result
        rows.append(CensusRow(consumer,depth,state,result))
    return tuple(rows)
