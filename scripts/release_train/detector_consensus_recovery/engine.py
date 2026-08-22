from .admission import admit_votes
from .budget import EvidenceBudget
from .consensus import decide
from .hysteresis import advance, HysteresisState
from .standing import calculate
from .persistence import candidates, select
from .authority import qualification_plan
from .receipt import issue

def qualify(*, subject, votes, generations, proofs, graph=None, dependency_standing=None, state=None, transactional=False):
    graph=graph or {subject.identity:()}; dependency_standing=dependency_standing or {}
    EvidenceBudget().admit(detectors=len(votes),observations=sum(g.calibration.support for g in generations),proofs=len(proofs))
    admitted=admit_votes(votes,generations); consensus=decide(admitted,proofs); next_state=advance(state or HysteresisState(),consensus)
    from .dependencies import blockers
    blocked=blockers(graph,dependency_standing).get(subject.identity,()); standing=calculate(consensus,next_state.regime,blocked); store=select(transactional_required=transactional)
    payload={"subject":subject.identity,"consensus":consensus.verdict,"regime":next_state.regime,"standing":standing,"blockers":list(blocked),"detectors":list(consensus.admitted_detectors),"store":store.kind,"store_candidates":[c.kind for c in candidates()],"phases":list(qualification_plan())}
    return {"consensus":consensus,"state":next_state,"standing":standing,"store":store,"receipt":issue(payload)}
