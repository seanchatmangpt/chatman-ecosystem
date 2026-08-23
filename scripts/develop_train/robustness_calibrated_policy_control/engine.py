from dataclasses import dataclass
from fractions import Fraction
from .calibration import calibrated_interval
from .shift import shift_adjust
from .independence import IndependenceProof
from .portfolio import Portfolio
from .pareto import Candidate,frontier
from .selector import Strategy,select
from .transition import PortfolioTransition
from .receipt import Receipt
from .ambiguity import classify,Topology
from .refusal import Refused
@dataclass(frozen=True)
class Evaluation:
    topology:Topology
    standing:str
    frontier:tuple[Candidate,...]
    selected:Candidate|None
    transition:PortfolioTransition|None
    receipt:Receipt
class RobustCompositionEngine:
    def evaluate(self,subject,bounds,calibration_frontier,proof:IndependenceProof,hypergraph,strategy:Strategy,shift_radius:Fraction,lipschitz:Fraction,max_size:int=2)->Evaluation:
        calibration=calibration_frontier.current()
        if not calibration.admitted(3,Fraction(4,5),Fraction(1,2)): raise Refused('UNCALIBRATED_BOUNDS')
        adjusted=[]
        for b in bounds:
            calibration_frontier.require(b.calibration_generation,b.calibration_digest)
            proof.require(b.evidence_ids)
            u=shift_adjust(calibrated_interval(b.utility,calibration,Fraction(1,2)),shift_radius,lipschitz)
            adjusted.append(type(b)(b.policy,u,b.breakdown_gamma,b.cost,b.latency,b.calibration_generation,b.calibration_digest,b.evidence_ids))
        portfolios=[]
        lookup={b.policy.digest:b for b in adjusted}
        for identities in hypergraph.maximal_feasible(tuple(b.policy for b in adjusted),max_size):
            p=Portfolio(tuple(lookup[i.digest] for i in identities)); n=len(p.members); weights=tuple(Fraction(1,n) for _ in p.members); agg=p.aggregate(weights)
            portfolios.append(Candidate(p.digest_key,agg.lower,agg.width,min(m.breakdown_gamma for m in p.members),p.cost,p.latency))
        pf=frontier(tuple(portfolios)); chosen=select(pf,strategy)
        topology=classify(tuple(adjusted)); standing='PARTIAL_ALIVE' if topology is Topology.DOMINANT and chosen else 'UNKNOWN'
        transition=None if chosen is None else PortfolioTransition(max(b.policy.generation for b in adjusted),max(b.policy.generation for b in adjusted)+1,chosen.key)
        r=Receipt(subject.value,max(b.policy.generation for b in adjusted),strategy.value,() if chosen is None else chosen.key,standing)
        return Evaluation(topology,standing,pf,chosen,transition,r)
