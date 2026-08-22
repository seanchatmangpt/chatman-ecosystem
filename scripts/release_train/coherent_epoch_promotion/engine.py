from __future__ import annotations
from .admission import admit_cut
from .authority import require
from .candidate import select_candidate
from .census import census
from .cut import EvidenceCut
from .dependency import DependencyGraph
from .epoch import EpochStamp
from .receipt import manufacture
from .standing import aggregate_standing
from .subject import Subject

def qualify(root: Subject, graph: DependencyGraph, cut: EvidenceCut, frontier: dict[str, EpochStamp], require_transactional: bool=False) -> dict:
    require('CONSTRUCT')
    order=admit_cut(root,graph,cut,frontier)
    rows=census(order,cut.observations)
    standing=aggregate_standing(rows)
    candidate=select_candidate(require_transactional)
    phases=('VERIFY','CONSTRUCT')
    payload={
        'root':root.key(), 'subjects':[s.key() for s in order],
        'epochs':[{'producer':e.producer.key(),'generation':e.generation,'event_id':e.event_id,'receipt':e.receipt} for e in sorted(cut.epochs,key=lambda e:e.producer.key())],
        'census':[{'subject':r.subject.key(),'state':r.state} for r in rows],
        'standing':standing,'persistence':candidate.persistence.value,'phases':list(phases),
    }
    receipt=manufacture(payload)
    return {**payload,'receipt_digest':receipt.digest,'actuation_performed':False}
