from __future__ import annotations
from collections import defaultdict
from .invalidation import Invalidation
from .witness import Witness
from .graph import DependencyGraph
from .subject import Subject

class AdmissionRefusal(ValueError):
    pass

_ORDER={"DELIVERED":0,"ACKNOWLEDGED":1,"DISCHARGED":2}

def admit(invalidation: Invalidation, graph: DependencyGraph, witnesses: tuple[Witness,...]) -> dict[Subject, tuple[Witness,...]]:
    affected = {subject for subject,_ in graph.affected(invalidation.producer)}
    by_consumer: dict[Subject,list[Witness]] = defaultdict(list)
    for witness in sorted(witnesses, key=lambda w:(w.consumer,w.at,_ORDER[w.state])):
        if witness.event_id != invalidation.event_id:
            raise AdmissionRefusal("REFUSED[FOREIGN_EVENT_WITNESS]")
        if witness.consumer not in affected:
            raise AdmissionRefusal("REFUSED[ORPHAN_CONSUMER_WITNESS]")
        if witness.at < invalidation.at:
            raise AdmissionRefusal("REFUSED[CAUSAL_TIME_INVERSION]")
        by_consumer[witness.consumer].append(witness)
    for consumer, rows in by_consumer.items():
        latest=-1
        seen=set()
        for row in rows:
            rank=_ORDER[row.state]
            if rank < latest:
                raise AdmissionRefusal("REFUSED[CAUSAL_REGRESSION]")
            key=(row.state,row.result)
            if key in seen:
                continue
            if rank > latest + 1:
                raise AdmissionRefusal("REFUSED[CAUSAL_GAP]")
            seen.add(key)
            latest=max(latest,rank)
    return {consumer:tuple(rows) for consumer,rows in sorted(by_consumer.items())}
