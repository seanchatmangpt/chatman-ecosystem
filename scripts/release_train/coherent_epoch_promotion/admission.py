from __future__ import annotations
from .cut import EvidenceCut
from .dependency import DependencyGraph
from .epoch import EpochStamp
from .subject import Subject

def admit_cut(root: Subject, graph: DependencyGraph, cut: EvidenceCut, frontier: dict[str, EpochStamp]) -> tuple[Subject, ...]:
    closure = graph.closure(root)
    selected = {e.producer for e in cut.epochs}
    missing = closure - selected
    if missing:
        raise ValueError('REFUSED[INCOMPLETE_DEPENDENCY_CUT]')
    for epoch in cut.epochs:
        current = frontier.get(epoch.producer.repo)
        if current is None:
            raise ValueError('REFUSED[UNKNOWN_PRODUCER_FRONTIER]')
        if epoch.identity() != current.identity():
            if epoch.generation < current.generation:
                raise ValueError('REFUSED[STALE_CUT_EPOCH]')
            raise ValueError('REFUSED[DIVERGENT_CURRENT_EPOCH]')
    return tuple(s for s in graph.order() if s in closure)
