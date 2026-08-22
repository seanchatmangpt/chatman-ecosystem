from dataclasses import dataclass
from .frontier import admit_frontier
from .admission import admit_evidence
from .selector import Score, score, select
from .standing import bounded_standing
from .receipt import issue

@dataclass(frozen=True)
class Qualification:
    selected_strategy: str|None
    standing: str
    phases: tuple
    receipt: object
    actuation_performed: bool=False

def qualify(subject, policy, frontier, evidence_by_strategy, metrics_by_strategy, dependency_graph, node):
    admit_frontier(frontier, policy)
    blockers=dependency_graph.blockers(node)
    accepted=[]
    drifted=False
    for strategy,evidence in sorted(evidence_by_strategy.items()):
        try:
            admit_evidence(evidence, policy)
            accepted.append(Score(strategy, score(strategy, **metrics_by_strategy[strategy]), evidence.support))
        except ValueError as exc:
            drifted = drifted or "POLICY_DRIFT" in str(exc)
    chosen=select(accepted).strategy if accepted and not blockers else None
    standing=bounded_standing(admitted=bool(chosen), blockers=blockers, drifted=drifted)
    body={"subject":subject.identity,"policy_generation":policy.generation,"policy_digest":policy.digest,"frontier_digest":frontier.digest,"selected_strategy":chosen,"blockers":blockers,"standing":standing,"phases":["VERIFY","CONSTRUCT"]}
    return Qualification(chosen, standing, ("VERIFY","CONSTRUCT"), issue(body))
