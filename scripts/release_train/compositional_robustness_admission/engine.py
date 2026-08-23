from dataclasses import dataclass
from fractions import Fraction
from .authority import ActionClass, admit
from .calibration import calibrated_interval
from .frontier import CalibrationFrontier
from .independence import IndependenceProof
from .policy_bound import PolicyBound
from .shift import shift_adjust
from .portfolio import Portfolio
from .pareto import frontier
from .strategy import Strategy, select
from .dependency import DependencyGraph
from .standing import standing
from .receipt import Receipt

@dataclass(frozen=True)
class Qualification:
    standing: str
    selected: Portfolio | None
    frontier: tuple[Portfolio,...]
    receipt: Receipt

def qualify(*, subject, bounds: tuple[PolicyBound,...], calibrations: CalibrationFrontier, independence: IndependenceProof, shift_radius: Fraction, lipschitz: Fraction, compatibility, dependency: DependencyGraph, root: str, strategy: Strategy, current: tuple[str,...]=()) -> Qualification:
    admit(ActionClass.SELECT); admit(ActionClass.CONSTRUCT); admit(ActionClass.VERIFY)
    current_cal=calibrations.current()
    adjusted=[]
    for b in bounds:
        calibrations.require(b.calibration_generation,b.calibration_digest)
        current_cal.admitted(3, Fraction(9,10), Fraction(10))
        adjusted.append(PolicyBound(b.policy, shift_adjust(calibrated_interval(b.interval,current_cal),shift_radius,lipschitz),b.breakdown_gamma,b.cost,b.latency,b.evidence,b.calibration_generation,b.calibration_digest))
    for i,a in enumerate(adjusted):
        for b in adjusted[i+1:]: independence.require(a.evidence,b.evidence)
    by_digest={b.policy.digest:b for b in adjusted}
    portfolios=[]
    for digests in compatibility.maximal_feasible(tuple(by_digest), max_size=min(3,len(by_digest))):
        members=tuple(by_digest[d] for d in digests); w=Fraction(1,len(members)); portfolios.append(Portfolio(members,tuple(w for _ in members)))
    pf=frontier(tuple(portfolios)); blockers=dependency.blockers(root)
    st=standing(blockers=blockers, calibrated=True, independent=True, frontier_nonempty=bool(pf))
    chosen=None if st!="PARTIAL_ALIVE" else select(pf,strategy,current)
    r=Receipt(f"{subject.repo}@{subject.sha}",strategy.value,() if chosen is None else chosen.digests,st,blockers)
    return Qualification(st,chosen,pf,r)
