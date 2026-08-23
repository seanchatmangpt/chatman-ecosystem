from dataclasses import dataclass
from .replica import ReplicaPolicyState
from .vector_clock import Relation
from .refusal import Refused
@dataclass(frozen=True)
class CausalFrontier:
    current:tuple[str,...]; historical:tuple[str,...]; concurrent:bool
def classify_frontier(states:list[ReplicaPolicyState])->CausalFrontier:
    if not states: raise Refused("EMPTY_REPLICA_SET")
    current=[]; historical=[]; concurrent=False
    for s in states:
        dominated=False
        for o in states:
            if s is o: continue
            rel=s.clock.compare(o.clock)
            if rel==Relation.BEFORE: dominated=True; break
            if rel==Relation.CONCURRENT: concurrent=True
        (historical if dominated else current).append(s)
    return CausalFrontier(tuple(sorted(s.replica_id for s in current)),tuple(sorted(s.replica_id for s in historical)),concurrent)
