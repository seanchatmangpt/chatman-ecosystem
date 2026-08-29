from dataclasses import dataclass
from .policy import admit_candidate
from .barrier import qualify_barrier
from .graph import DependencyGraph
from .risk import RiskVector
from .rollout import build_rollout
from .rollback import RollbackPlan
from .receipt import manufacture, replay
@dataclass(frozen=True)
class CandidateEvidence:
    ancestry_proven:bool
    source_allowed:bool
    advisory_clear:bool
    gates:dict
    risk:RiskVector
def manufacture_epoch(predecessor_sha, subject_sha, candidates, evidence_by_component, edges=()):
    admitted=[]
    for c in candidates:
        e=evidence_by_component[c.component]
        admit_candidate(c,e.ancestry_proven,e.source_allowed,e.advisory_clear)
        standing,_=qualify_barrier(e.gates)
        if standing != "ALIVE": continue
        admitted.append((e.risk.score,c.component,c))
    if not admitted: raise ValueError("BLOCKED[NO_QUALIFIED_PROMOTION]")
    admitted.sort(key=lambda x:(-x[0],x[1]))
    selected_components=tuple(x[1] for x in admitted)
    order=DependencyGraph(edges).order(selected_components)
    rollout=build_rollout(order)
    selected_map={c.component:c for _,_,c in admitted}
    rollbacks=tuple(RollbackPlan(selected_map[c].current.sha, selected_map[c].proposed.sha,"python3 -m unittest discover -s tests/release_train/promotion_epoch -p 'test_*.py' -v") for c in order)
    receipt=manufacture(predecessor_sha,subject_sha,order,"ALIVE")
    if not replay(receipt): raise ValueError("REFUSED[RECEIPT_REPLAY_FAILED]")
    return {"order":order,"rollout":rollout,"rollback":rollbacks,"receipt":receipt,"actuation_performed":False}
