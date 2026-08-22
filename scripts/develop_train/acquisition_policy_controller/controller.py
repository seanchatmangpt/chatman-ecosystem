from dataclasses import dataclass
from .authority import ActionClass,admit_action
from .drift import DriftState,page_hinkley
from .evidence import aggregate
from .frontier import admit_frontier
from .receipt import issue
from .selector import score,select
from .standing import bounded_standing
from .state import PolicyState,StateToken
from .subject import Refusal
@dataclass(frozen=True,slots=True)
class Qualification:
    selected_strategy:str|None
    standing:str
    drifted:bool
    blockers:tuple
    receipt:object
@dataclass(frozen=True,slots=True)
class CommittedQualification:
    qualification:Qualification
    state:PolicyState
def qualify(subject,policy,rows,frontier,dependencies,node,current_generation,*,receipt_parent=None):
    admit_action(ActionClass.SELECT)
    if any(r.subject!=subject for r in rows): raise Refusal("REFUSED_FOREIGN_REALIZATION")
    if any(r.policy_generation!=policy.generation for r in rows): raise Refusal("REFUSED_STALE_REALIZATION_GENERATION")
    admit_frontier(frontier,policy,current_generation)
    ev=aggregate(rows); total=sum(e.utility.n for e in ev.values()); scores=[score(e,total,policy) for e in ev.values()]
    try: chosen=select(scores)
    except Refusal: chosen=None
    drift=DriftState()
    for r in sorted(rows,key=lambda x:(x.observed_at,x.candidate_id)): drift=page_hinkley(drift,r.realized_gain-r.predicted_gain,threshold=0.4)
    blockers=dependencies.blockers(node); standing=bounded_standing(selected=chosen is not None,drifted=drift.drifted,blockers=blockers)
    rec=issue(subject,policy_generation=policy.generation,policy_digest=policy.digest,frontier_digest=frontier.digest,selected_strategy=chosen.strategy if chosen else None,standing=standing,parent=receipt_parent)
    return Qualification(chosen.strategy if chosen else None,standing,drift.drifted,blockers,rec)
def qualify_and_commit(subject,policy,rows,frontier,dependencies,node,current_generation,store,expected_token:StateToken|None):
    parent=expected_token.digest if expected_token else None
    qualification=qualify(subject,policy,rows,frontier,dependencies,node,current_generation,receipt_parent=parent)
    candidate=PolicyState.from_qualification(subject,policy,frontier,qualification,expected_token)
    committed=store.compare_and_swap(subject,expected_token,candidate)
    return CommittedQualification(qualification,committed)
