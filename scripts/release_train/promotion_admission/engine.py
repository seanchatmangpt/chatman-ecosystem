from __future__ import annotations
from dataclasses import dataclass
from .admission import admit_subject
from .authority import admit_action
from .candidate import PromotionCandidate, preserve_frontier
from .dependency import DependencyGraph
from .evidence import Evidence, normalize_vector
from .plan import build_plan
from .quorum import evaluate_quorum
from .receipt import manufacture_receipt
from .requirements import ReleaseProfile
from .rollback import RollbackBoundary
from .subject import Subject

@dataclass(frozen=True)
class PromotionResult:
    standing: str
    selected_candidate: str | None
    plan: tuple
    receipt: dict

def manufacture_promotion(candidates: list[PromotionCandidate], graph: DependencyGraph,
                          evidence: dict[Subject, list[Evidence]], profile: ReleaseProfile,
                          predecessor_sha: str) -> PromotionResult:
    admit_action("SELECT")
    frontier=preserve_frontier(candidates)
    if not frontier:
        body={"predecessor_sha":predecessor_sha,"selected_candidate":None,"standing":"BLOCKED","subjects":[],"actuation_performed":False}
        return PromotionResult("BLOCKED",None,(),manufacture_receipt(body))
    selected=frontier[0]
    order=graph.closure(frozenset({selected.root})); graph.assert_closed(frozenset(order))
    admissions={}
    for subject in order:
        vector=normalize_vector(subject,evidence.get(subject,[]))
        admissions[subject]=admit_subject(subject,vector,profile)
    quorum=evaluate_quorum(order,admissions)
    if quorum.blocked:
        body={"predecessor_sha":predecessor_sha,"selected_candidate":selected.candidate_id,"standing":"BLOCKED",
              "subjects":[s.identity for s in order],"blocked":[s.identity for s in quorum.blocked],"actuation_performed":False}
        return PromotionResult("BLOCKED",selected.candidate_id,(),manufacture_receipt(body))
    admit_action("CONSTRUCT")
    plan=build_plan(order); RollbackBoundary(predecessor_sha,order)
    body={"predecessor_sha":predecessor_sha,"selected_candidate":selected.candidate_id,"standing":"PARTIAL_ALIVE",
          "subjects":[s.identity for s in order],"plan":[{"phase":p.phase,"subject":p.subject.identity,"action":p.action} for p in plan],
          "actuation_performed":False}
    return PromotionResult("PARTIAL_ALIVE",selected.candidate_id,plan,manufacture_receipt(body))
