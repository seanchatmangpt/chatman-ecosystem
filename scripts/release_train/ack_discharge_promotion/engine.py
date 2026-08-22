from __future__ import annotations
from .invalidation import Invalidation
from .graph import DependencyGraph
from .witness import Witness
from .admission import admit
from .census import census
from .strategy import Strategy
from .standing import standing
from .candidate import select
from .authority import require
from .receipt import manufacture

def qualify(*, invalidation: Invalidation, graph: DependencyGraph, witnesses: tuple[Witness,...], strategy: Strategy,
            require_durable: bool=False, require_transactional: bool=False) -> dict:
    admitted=admit(invalidation,graph,witnesses)
    rows=census(invalidation,graph,admitted)
    affected=tuple(row.consumer for row in rows)
    discharged={row.consumer for row in rows if row.state in {"REQUALIFIED","BLOCKED","UNSUPPORTED"}}
    complete=strategy.complete(discharged,affected)
    current_standing=standing(rows,complete)
    candidate=select(require_durable=require_durable,require_transactional=require_transactional)
    require("CONSTRUCT")
    plan={"phases":["VERIFY","CONSTRUCT"],"candidate":candidate.name,"strategy":strategy.kind,"standing":current_standing}
    body={
        "producer":invalidation.producer.render(),
        "event_id":invalidation.event_id,
        "census":[{"consumer":r.consumer.render(),"depth":r.depth,"state":r.state,"result":r.result} for r in rows],
        "plan":plan,
    }
    receipt=manufacture(body)
    return {"standing":current_standing,"complete":complete,"candidate":candidate.name,"plan":plan,
            "receipt":{"schema":receipt.schema,"digest":receipt.digest,"body":receipt.body}}
